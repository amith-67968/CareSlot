-- CareSlot Smart Appointment Booking migration
-- Run in Supabase SQL Editor after the base setup_supabase.sql script.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Expand appointment lifecycle for direct API and fallback booking flows.
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_status_check;
ALTER TABLE appointments ADD CONSTRAINT appointments_status_check
CHECK (status IN (
    'pending_confirmation',
    'scheduled',
    'confirmed',
    'completed',
    'cancelled',
    'no-show',
    'rescheduled'
));

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS doctor_id TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS doctor_rating FLOAT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS doctor_experience_years INT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS consultation_fee NUMERIC(10,2);
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS appointment_reason TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS symptoms_notes TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS follow_up_details TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booking_mode TEXT DEFAULT 'fallback_internal'
    CHECK (booking_mode IN ('direct_api', 'fallback_internal'));
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booking_confirmation_status TEXT DEFAULT 'pending_hospital_confirmation'
    CHECK (booking_confirmation_status IN (
        'confirmed',
        'pending_hospital_confirmation',
        'api_retry_required',
        'reschedule_requested',
        'cancelled',
        'completed'
    ));
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS external_appointment_id TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS external_provider TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS api_payload JSONB DEFAULT '{}';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_status TEXT DEFAULT 'pending'
    CHECK (reminder_status IN ('pending', 'sent', 'cancelled', 'failed'));
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS reminder_channels TEXT[] DEFAULT ARRAY['email','sms'];
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS hospital_staff_notified_at TIMESTAMPTZ;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS rescheduled_from UUID REFERENCES appointments(id);
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMPTZ;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_appointments_place_doctor_date
ON appointments(hospital_place_id, doctor_id, appointment_date, appointment_time);

CREATE INDEX IF NOT EXISTS idx_appointments_booking_status
ON appointments(user_id, booking_mode, booking_confirmation_status);

-- Optional direct API registry. Keep API secrets server-side only.
CREATE TABLE IF NOT EXISTS hospital_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_place_id TEXT UNIQUE NOT NULL,
    hospital_name TEXT NOT NULL,
    provider_name TEXT,
    base_url TEXT NOT NULL,
    api_key_secret_name TEXT,
    doctors_endpoint TEXT DEFAULT '/doctors',
    slots_endpoint TEXT DEFAULT '/slots',
    booking_endpoint TEXT DEFAULT '/appointments',
    cancel_endpoint TEXT,
    reschedule_endpoint TEXT,
    supports_patient_registration BOOLEAN DEFAULT true,
    supports_real_time_slots BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Manual confirmation queue for hospitals without direct APIs.
CREATE TABLE IF NOT EXISTS hospital_booking_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    hospital_place_id TEXT,
    hospital_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending_staff_confirmation'
        CHECK (status IN ('pending_staff_confirmation', 'notified', 'confirmed', 'declined', 'expired')),
    staff_notification_status TEXT DEFAULT 'pending'
        CHECK (staff_notification_status IN ('pending', 'sent', 'failed')),
    request_payload JSONB DEFAULT '{}',
    staff_notes TEXT,
    confirmed_slot JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE hospital_booking_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users read own booking requests" ON hospital_booking_requests;
CREATE POLICY "Users read own booking requests"
ON hospital_booking_requests FOR SELECT
USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_hospital_booking_requests_status
ON hospital_booking_requests(hospital_place_id, status, created_at);

CREATE INDEX IF NOT EXISTS idx_hospital_booking_requests_user
ON hospital_booking_requests(user_id, created_at);

-- Reminder delivery fields for email/SMS/WhatsApp-ready architecture.
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS delivery_channels TEXT[] DEFAULT ARRAY['email','sms'];
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS email_status TEXT DEFAULT 'pending'
    CHECK (email_status IN ('pending', 'sent', 'failed', 'disabled', 'not_configured', 'skipped'));
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS sms_status TEXT DEFAULT 'pending'
    CHECK (sms_status IN ('pending', 'sent', 'failed', 'disabled', 'not_configured', 'skipped'));
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS whatsapp_status TEXT DEFAULT 'skipped'
    CHECK (whatsapp_status IN ('pending', 'sent', 'failed', 'disabled', 'not_configured', 'skipped'));
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ;
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE INDEX IF NOT EXISTS idx_reminders_due_delivery
ON reminders(status, scheduled_at, reminder_type);

-- Keep updated_at fresh on the new queue table.
DROP TRIGGER IF EXISTS update_hospital_booking_requests_updated_at ON hospital_booking_requests;
CREATE TRIGGER update_hospital_booking_requests_updated_at
    BEFORE UPDATE ON hospital_booking_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
