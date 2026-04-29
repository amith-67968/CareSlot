-- ============================================
-- CareSlot — Supabase Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── 1. User Profiles ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    date_of_birth DATE,
    gender TEXT CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    blood_group TEXT,
    avatar_url TEXT,
    address JSONB DEFAULT '{}',
    emergency_contact JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 2. Appointments ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    doctor_name TEXT NOT NULL,
    doctor_specialty TEXT,
    hospital_name TEXT NOT NULL,
    hospital_address TEXT,
    hospital_place_id TEXT,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    consultation_type TEXT CHECK (consultation_type IN ('in-person', 'video', 'phone')) DEFAULT 'in-person',
    status TEXT CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no-show')) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 3. Medical History ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS medical_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    condition_name TEXT NOT NULL,
    diagnosed_date DATE,
    status TEXT CHECK (status IN ('active', 'resolved', 'chronic')) DEFAULT 'active',
    medications JSONB DEFAULT '[]',
    allergies TEXT[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 4. Chatbot History ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chatbot_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 5. Uploaded Images ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS uploaded_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    public_url TEXT,
    image_type TEXT CHECK (image_type IN ('skin', 'report', 'prescription', 'other')) DEFAULT 'skin',
    prediction_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 6. Notifications ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    type TEXT CHECK (type IN ('appointment', 'follow_up', 'medicine', 'health_check', 'general')) NOT NULL,
    is_read BOOLEAN DEFAULT false,
    reference_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 7. Reminders ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    reminder_type TEXT CHECK (reminder_type IN ('appointment', 'follow_up', 'medicine', 'health_check')) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT CHECK (status IN ('pending', 'sent', 'cancelled')) DEFAULT 'pending',
    reference_id UUID,
    recurrence TEXT CHECK (recurrence IN ('none', 'daily', 'weekly', 'monthly')) DEFAULT 'none',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 8. Disease Predictions ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS disease_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prediction_type TEXT CHECK (prediction_type IN ('symptom_chat', 'skin_detection')) NOT NULL,
    input_symptoms TEXT[] DEFAULT '{}',
    image_id UUID REFERENCES uploaded_images(id),
    predicted_condition TEXT,
    confidence_score FLOAT,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    precautions TEXT[] DEFAULT '{}',
    home_remedies TEXT[] DEFAULT '{}',
    recommended_specialist TEXT,
    ai_response JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─── 9. PCOD Assessments ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pcod_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    questionnaire_responses JSONB NOT NULL,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')) NOT NULL,
    risk_score FLOAT,
    conditions_flagged TEXT[] DEFAULT '{}',
    precautions TEXT[] DEFAULT '{}',
    recommendations TEXT[] DEFAULT '{}',
    recommended_specialist TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);


-- ═══════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ═══════════════════════════════════════════════════════════════════════

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploaded_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE disease_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pcod_assessments ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own data
CREATE POLICY "Users CRUD own profile" ON user_profiles FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own appointments" ON appointments FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own medical history" ON medical_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own chat history" ON chatbot_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own images" ON uploaded_images FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own notifications" ON notifications FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own reminders" ON reminders FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own predictions" ON disease_predictions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users CRUD own assessments" ON pcod_assessments FOR ALL USING (auth.uid() = user_id);


-- ═══════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════

CREATE INDEX idx_appointments_user_date ON appointments(user_id, appointment_date);
CREATE INDEX idx_chatbot_history_session ON chatbot_history(user_id, session_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_reminders_user_status ON reminders(user_id, status, scheduled_at);
CREATE INDEX idx_predictions_user_type ON disease_predictions(user_id, prediction_type);
CREATE INDEX idx_pcod_user ON pcod_assessments(user_id);


-- ═══════════════════════════════════════════════════════════════════════
-- STORAGE BUCKET
-- ═══════════════════════════════════════════════════════════════════════

-- Run this separately or via Supabase Dashboard:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('skin-uploads', 'skin-uploads', true);


-- ═══════════════════════════════════════════════════════════════════════
-- FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
