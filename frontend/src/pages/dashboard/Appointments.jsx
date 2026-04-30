import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Ban,
  BellRing,
  Building2,
  CalendarCheck,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock,
  DollarSign,
  History,
  Loader2,
  MapPin,
  Navigation,
  Phone,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Stethoscope,
  Video,
  X,
} from 'lucide-react';
import { appointmentAPI, doctorAPI } from '../../services/api';

const STATUS_META = {
  pending_confirmation: { label: 'Pending', tone: 'bg-amber-50 text-amber-700 border-amber-200' },
  scheduled: { label: 'Scheduled', tone: 'bg-blue-50 text-blue-700 border-blue-200' },
  confirmed: { label: 'Confirmed', tone: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  completed: { label: 'Completed', tone: 'bg-slate-100 text-slate-600 border-slate-200' },
  cancelled: { label: 'Cancelled', tone: 'bg-rose-50 text-rose-700 border-rose-200' },
  rescheduled: { label: 'Rescheduled', tone: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
};

const TYPE_ICONS = { 'in-person': MapPin, video: Video, phone: Phone };

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'today', label: 'Today' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
];

function localDateInput(date = new Date()) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function formatDate(value) {
  if (!value) return '';
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(value) {
  if (!value) return '';
  const raw = String(value).slice(0, 5);
  const [hourRaw, minute] = raw.split(':');
  const hour = Number(hourRaw);
  if (Number.isNaN(hour)) return raw;
  const hour12 = hour % 12 || 12;
  return `${hour12}:${minute} ${hour >= 12 ? 'PM' : 'AM'}`;
}

function bookingLabel(mode, confirmationStatus) {
  if (mode === 'direct_api') return 'Direct API';
  if (confirmationStatus === 'api_retry_required') return 'Staff retry';
  return 'Internal confirmation';
}

function Toast({ toast }) {
  if (!toast) return null;
  const Icon = toast.type === 'error' ? AlertTriangle : CheckCircle2;
  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold shadow-xl ${
      toast.type === 'error'
        ? 'border-rose-200 bg-white text-rose-700'
        : 'border-emerald-200 bg-white text-emerald-700'
    }`}>
      <Icon size={17} />
      {toast.message}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="h-36 rounded-2xl bg-slate-100" />
      <div className="mt-4 h-4 w-2/3 rounded bg-slate-100" />
      <div className="mt-3 h-3 w-full rounded bg-slate-100" />
      <div className="mt-2 h-3 w-4/5 rounded bg-slate-100" />
    </div>
  );
}

function HospitalImage({ hospital }) {
  const [failed, setFailed] = useState(false);
  const photoRef = hospital?.photos?.[0]?.photo_reference;

  if (photoRef && !failed) {
    return (
      <img
        src={doctorAPI.photoUrl(photoRef, 900)}
        alt={hospital.name}
        className="h-36 w-full rounded-2xl object-cover"
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <div className="flex h-36 w-full items-center justify-center rounded-2xl bg-gradient-to-br from-blue-50 via-white to-cyan-50 text-blue-600">
      <Building2 size={34} />
    </div>
  );
}

export default function Appointments() {
  const location = useLocation();
  const seededSpecialty = location.state?.recommendedSpecialty || location.state?.specialistKey || '';
  const seededSymptoms = location.state?.symptoms || '';

  const [appointments, setAppointments] = useState([]);
  const [stats, setStats] = useState({ upcoming: 0, today: 0, completed: 0, cancelled: 0, pending_confirmation: 0 });
  const [filter, setFilter] = useState('upcoming');
  const [historyLoading, setHistoryLoading] = useState(true);

  const [recommendation, setRecommendation] = useState(null);
  const [symptoms, setSymptoms] = useState(seededSymptoms);
  const [specialty, setSpecialty] = useState(seededSpecialty);
  const [radius, setRadius] = useState(7000);

  const [coords, setCoords] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  const [hospitalLoading, setHospitalLoading] = useState(false);
  const [hospitalError, setHospitalError] = useState('');
  const [selectedHospital, setSelectedHospital] = useState(null);

  const [doctors, setDoctors] = useState([]);
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [doctorError, setDoctorError] = useState('');

  const [bookingDoctor, setBookingDoctor] = useState(null);
  const [rescheduleTarget, setRescheduleTarget] = useState(null);
  const [bookingForm, setBookingForm] = useState({
    appointment_date: localDateInput(),
    appointment_time: '',
    consultation_type: 'in-person',
    appointment_reason: '',
    symptoms_notes: seededSymptoms,
    follow_up_details: '',
  });
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadAppointments = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const [list, counts] = await Promise.all([appointmentAPI.list(), appointmentAPI.stats()]);
      setAppointments(list.appointments || []);
      setStats(counts || {});
    } catch (err) {
      showToast(err.message || 'Could not load appointments', 'error');
    } finally {
      setHistoryLoading(false);
    }
  }, [showToast]);

  const loadRecommendation = useCallback(async (nextSymptoms = '') => {
    try {
      const result = await appointmentAPI.recommendSpecialist({
        symptoms: nextSymptoms || undefined,
        diagnosis_type: seededSpecialty ? 'symptoms' : undefined,
      });
      setRecommendation(result);
      setSpecialty(result.specialist_key);
      return result;
    } catch {
      const fallback = {
        specialist_key: seededSpecialty || 'general_physician',
        specialist_label: seededSpecialty ? seededSpecialty.replace('_', ' ') : 'General Physician',
        confidence: 0.62,
        reason: 'Start with primary triage and refine by symptoms.',
        source: 'default',
      };
      setRecommendation(fallback);
      setSpecialty(fallback.specialist_key);
      return fallback;
    }
  }, [seededSpecialty]);

  useEffect(() => {
    loadAppointments();
    loadRecommendation(seededSymptoms);
  }, [loadAppointments, loadRecommendation, seededSymptoms]);

  const getLocation = useCallback(() => new Promise((resolve, reject) => {
    if (coords) return resolve(coords);
    if (!navigator.geolocation) return reject(new Error('Location access is not available in this browser.'));
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const next = { lat: position.coords.latitude, lng: position.coords.longitude };
        setCoords(next);
        resolve(next);
      },
      () => reject(new Error('Location permission is needed to show nearby hospitals.')),
      { timeout: 10000 },
    );
  }), [coords]);

  const searchHospitals = useCallback(async (overrideSpecialty) => {
    setHospitalLoading(true);
    setHospitalError('');
    setSelectedHospital(null);
    setDoctors([]);
    try {
      const loc = await getLocation();
      const targetSpecialty = overrideSpecialty || specialty || recommendation?.specialist_key || 'general_physician';
      const result = await appointmentAPI.findHospitals(loc.lat, loc.lng, targetSpecialty, radius);
      setHospitals(result.results || []);
      if ((result.results || []).length === 0) {
        setHospitalError('No hospitals found nearby for this specialty. Try a wider radius.');
      }
    } catch (err) {
      setHospitalError(err.message || 'Unable to search nearby hospitals.');
    } finally {
      setHospitalLoading(false);
    }
  }, [getLocation, radius, recommendation, specialty]);

  const refineRecommendation = async () => {
    const result = await loadRecommendation(symptoms);
    await searchHospitals(result.specialist_key);
  };

  const selectHospital = async (hospital) => {
    setSelectedHospital(hospital);
    setDoctorLoading(true);
    setDoctorError('');
    setDoctors([]);
    try {
      const result = await appointmentAPI.getHospitalDoctors(
        hospital.place_id,
        specialty,
        hospital.name,
        hospital.address,
      );
      setSelectedHospital(result.hospital || hospital);
      setDoctors(result.doctors || []);
    } catch (err) {
      setDoctorError(err.message || 'Could not load doctors for this hospital.');
    } finally {
      setDoctorLoading(false);
    }
  };

  const openBooking = (doctor) => {
    setBookingDoctor(doctor);
    setRescheduleTarget(null);
    setBookingForm({
      appointment_date: localDateInput(),
      appointment_time: '',
      consultation_type: doctor.consultation_types?.[0] || 'in-person',
      appointment_reason: recommendation?.specialist_label ? `${recommendation.specialist_label} consultation` : '',
      symptoms_notes: symptoms || recommendation?.diagnosis_context?.condition || '',
      follow_up_details: '',
    });
    setSlots([]);
  };

  const openReschedule = (appointment) => {
    setRescheduleTarget(appointment);
    setBookingDoctor(null);
    setBookingForm({
      appointment_date: appointment.appointment_date || localDateInput(),
      appointment_time: '',
      consultation_type: appointment.consultation_type || 'in-person',
      appointment_reason: appointment.appointment_reason || '',
      symptoms_notes: appointment.symptoms_notes || appointment.notes || '',
      follow_up_details: appointment.follow_up_details || '',
    });
    setSlots([]);
  };

  useEffect(() => {
    const activeDoctor = bookingDoctor || rescheduleTarget;
    if (!activeDoctor || !bookingForm.appointment_date) return;

    let cancelled = false;
    setSlotsLoading(true);
    setBookingForm((prev) => ({ ...prev, appointment_time: '' }));

    appointmentAPI.getSlots(
      bookingForm.appointment_date,
      activeDoctor.doctor_name || activeDoctor.name,
      bookingForm.consultation_type,
      activeDoctor.hospital_place_id || selectedHospital?.place_id,
      activeDoctor.doctor_id || activeDoctor.id,
    )
      .then((result) => {
        if (!cancelled) setSlots(result.slots || []);
      })
      .catch(() => {
        if (!cancelled) setSlots([]);
      })
      .finally(() => {
        if (!cancelled) setSlotsLoading(false);
      });

    return () => { cancelled = true; };
  }, [
    bookingDoctor,
    bookingForm.appointment_date,
    bookingForm.consultation_type,
    rescheduleTarget,
    selectedHospital?.place_id,
  ]);

  const closeModal = () => {
    setBookingDoctor(null);
    setRescheduleTarget(null);
    setSlots([]);
  };

  const confirmBooking = async () => {
    if (!bookingDoctor || !selectedHospital || !bookingForm.appointment_time) return;
    setSaving(true);
    try {
      const payload = {
        doctor_id: bookingDoctor.id,
        doctor_name: bookingDoctor.name,
        doctor_specialty: bookingDoctor.specialization,
        doctor_rating: bookingDoctor.rating,
        doctor_experience_years: bookingDoctor.experience_years,
        consultation_fee: bookingDoctor.consultation_fee,
        hospital_name: selectedHospital.name,
        hospital_address: selectedHospital.address,
        hospital_place_id: selectedHospital.place_id,
        ...bookingForm,
        source_context: {
          specialist_recommendation: recommendation,
          hospital_booking_mode: selectedHospital.booking_mode,
        },
      };
      const created = await appointmentAPI.create(payload);
      showToast(
        created.booking_mode === 'direct_api'
          ? 'Appointment confirmed with the hospital.'
          : 'Appointment request sent for hospital confirmation.',
      );
      closeModal();
      await loadAppointments();
    } catch (err) {
      showToast(err.message || 'Booking failed. Please retry.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const confirmReschedule = async () => {
    if (!rescheduleTarget || !bookingForm.appointment_time) return;
    setSaving(true);
    try {
      await appointmentAPI.reschedule(rescheduleTarget.id, {
        appointment_date: bookingForm.appointment_date,
        appointment_time: bookingForm.appointment_time,
        reason: bookingForm.follow_up_details || 'Patient requested reschedule',
      });
      showToast('Appointment reschedule request saved.');
      closeModal();
      await loadAppointments();
    } catch (err) {
      showToast(err.message || 'Reschedule failed. Please retry.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const cancelAppointment = async (appointment) => {
    if (!window.confirm('Cancel this appointment?')) return;
    try {
      await appointmentAPI.cancel(appointment.id);
      showToast('Appointment cancelled.');
      await loadAppointments();
    } catch (err) {
      showToast(err.message || 'Cancellation failed.', 'error');
    }
  };

  const quickRebook = async (appointment) => {
    setSymptoms(appointment.symptoms_notes || appointment.notes || '');
    setSpecialty(appointment.doctor_specialty?.toLowerCase().replaceAll(' ', '_') || specialty);
    setHospitalLoading(false);
    setSelectedHospital({
      place_id: appointment.hospital_place_id,
      name: appointment.hospital_name,
      address: appointment.hospital_address,
      booking_mode: appointment.booking_mode || 'fallback_internal',
    });
    openBooking({
      id: appointment.doctor_id || appointment.doctor_name,
      name: appointment.doctor_name,
      specialization: appointment.doctor_specialty || 'Specialist',
      rating: appointment.doctor_rating,
      experience_years: appointment.doctor_experience_years,
      consultation_fee: appointment.consultation_fee,
      hospital_place_id: appointment.hospital_place_id,
      consultation_types: [appointment.consultation_type || 'in-person'],
    });
  };

  const today = localDateInput();
  const visibleAppointments = useMemo(() => appointments.filter((appointment) => {
    const day = appointment.appointment_date;
    if (filter === 'all') return true;
    if (filter === 'today') return day === today && appointment.status !== 'cancelled';
    if (filter === 'upcoming') return day >= today && !['cancelled', 'completed'].includes(appointment.status);
    return appointment.status === filter;
  }), [appointments, filter, today]);

  const modalOpen = bookingDoctor || rescheduleTarget;
  const modalTitle = rescheduleTarget ? 'Reschedule Appointment' : 'Confirm Appointment';
  const activeDoctor = bookingDoctor || rescheduleTarget;
  const ActiveTypeIcon = TYPE_ICONS[bookingForm.consultation_type] || MapPin;

  return (
    <div className="min-h-full space-y-6 text-slate-950">
      <Toast toast={toast} />

      <section className="rounded-3xl border border-blue-100 bg-white p-5 shadow-sm shadow-blue-100/70 sm:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-blue-700">
              <Sparkles size={14} />
              Smart Booking
            </div>
            <h1 className="text-2xl font-black tracking-tight text-slate-950 sm:text-3xl">
              Diagnosis to confirmed care, inside CareSlot
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Discover nearby hospitals, compare specialists, pick a live slot, and keep the booking record in one healthcare workspace.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 lg:w-160">
            {[
              { label: 'Upcoming', value: stats.upcoming || 0, Icon: CalendarDays, tone: 'text-blue-700 bg-blue-50' },
              { label: 'Today', value: stats.today || 0, Icon: Clock, tone: 'text-cyan-700 bg-cyan-50' },
              { label: 'Pending', value: stats.pending_confirmation || 0, Icon: BellRing, tone: 'text-amber-700 bg-amber-50' },
              { label: 'Done', value: stats.completed || 0, Icon: ShieldCheck, tone: 'text-emerald-700 bg-emerald-50' },
              { label: 'Cancelled', value: stats.cancelled || 0, Icon: Ban, tone: 'text-rose-700 bg-rose-50' },
            ].map(({ label, value, Icon, tone }) => (
              <div key={label} className="rounded-2xl border border-slate-100 bg-slate-50 p-3">
                <div className={`mb-2 flex h-8 w-8 items-center justify-center rounded-xl ${tone}`}>
                  <Icon size={16} />
                </div>
                <div className="text-xl font-black">{value}</div>
                <div className="text-xs font-semibold text-slate-500">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-1">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/20">
              <Activity size={20} />
            </div>
            <div>
              <h2 className="text-base font-black text-slate-950">AI Recommended Specialist</h2>
              <p className="mt-1 text-sm text-slate-500">{recommendation?.reason || 'Analyzing recent health context...'}</p>
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-blue-100 bg-blue-50 p-4">
            <div className="text-xs font-bold uppercase tracking-wide text-blue-700">Best match</div>
            <div className="mt-1 flex items-center justify-between gap-3">
              <div>
                <div className="text-xl font-black text-slate-950">{recommendation?.specialist_label || 'General Physician'}</div>
                <div className="text-sm font-semibold text-blue-700">
                  {Math.round((recommendation?.confidence || 0.62) * 100)}% confidence
                </div>
              </div>
              <Stethoscope className="text-blue-600" size={30} />
            </div>
          </div>

          <label className="mt-5 block text-sm font-bold text-slate-700" htmlFor="symptom-notes">
            Symptoms or concern
          </label>
          <textarea
            id="symptom-notes"
            value={symptoms}
            onChange={(event) => setSymptoms(event.target.value)}
            rows={4}
            className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
            placeholder="Skin rash, irregular periods, chest discomfort..."
          />

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <button
              type="button"
              onClick={refineRecommendation}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-blue-700 px-4 py-3 text-sm font-black text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-800"
            >
              <Search size={16} />
              Search Care
            </button>
            <button
              type="button"
              onClick={() => searchHospitals()}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              <Navigation size={16} />
              Nearby Hospitals
            </button>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-black text-slate-950">Nearby Hospitals</h2>
              <p className="text-sm text-slate-500">
                {specialty ? `Prioritizing ${specialty.replace('_', ' ')}` : 'Choose a recommended specialty to begin'}
              </p>
            </div>
            <select
              value={radius}
              onChange={(event) => setRadius(Number(event.target.value))}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-blue-400"
            >
              <option value={3000}>3 km</option>
              <option value={7000}>7 km</option>
              <option value={12000}>12 km</option>
              <option value={25000}>25 km</option>
            </select>
          </div>

          {hospitalError && (
            <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 sm:flex-row sm:items-center sm:justify-between">
              <span>{hospitalError}</span>
              <button type="button" onClick={() => searchHospitals()} className="inline-flex items-center gap-2 font-black">
                <RefreshCw size={14} /> Retry
              </button>
            </div>
          )}

          {hospitalLoading ? (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : hospitals.length === 0 ? (
            <div className="mt-5 rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
              <MapPin className="mx-auto text-slate-400" size={36} />
              <h3 className="mt-3 text-base font-black text-slate-800">No hospital search yet</h3>
              <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-slate-500">
                Nearby hospitals and clinics will appear with availability and booking status.
              </p>
              <button
                type="button"
                onClick={() => searchHospitals()}
                className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-blue-700 px-4 py-3 text-sm font-black text-white transition hover:bg-blue-800"
              >
                <Navigation size={16} />
                Find Nearby Hospitals
              </button>
            </div>
          ) : (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {hospitals.map((hospital) => (
                <article
                  key={hospital.place_id}
                  className={`rounded-3xl border bg-white p-3 shadow-sm transition hover:-translate-y-1 hover:shadow-lg ${
                    selectedHospital?.place_id === hospital.place_id ? 'border-blue-300 ring-4 ring-blue-100' : 'border-slate-200'
                  }`}
                >
                  <HospitalImage hospital={hospital} />
                  <div className="p-2">
                    <div className="mt-2 flex items-start justify-between gap-3">
                      <h3 className="text-base font-black leading-tight text-slate-950">{hospital.name}</h3>
                      {hospital.is_open_now !== null && hospital.is_open_now !== undefined && (
                        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-black ${
                          hospital.is_open_now ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'
                        }`}>
                          {hospital.is_open_now ? 'Open' : 'Closed'}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 flex items-start gap-2 text-sm leading-5 text-slate-500">
                      <MapPin size={15} className="mt-0.5 shrink-0 text-blue-500" />
                      {hospital.address}
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-bold">
                      {hospital.rating && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-amber-700">
                          <Star size={13} className="fill-amber-400 text-amber-400" /> {hospital.rating}
                        </span>
                      )}
                      {hospital.distance_text && (
                        <span className="rounded-full bg-cyan-50 px-2.5 py-1 text-cyan-700">{hospital.distance_text}</span>
                      )}
                      <span className={`rounded-full px-2.5 py-1 ${
                        hospital.booking_mode === 'direct_api' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'
                      }`}>
                        {bookingLabel(hospital.booking_mode)}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(hospital.specialties_available || []).slice(0, 3).map((item) => (
                        <span key={item} className="rounded-full border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600">
                          {item}
                        </span>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => selectHospital(hospital)}
                      className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-black text-white transition hover:bg-blue-800"
                    >
                      View Doctors
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-black text-slate-950">Doctors {selectedHospital ? `at ${selectedHospital.name}` : ''}</h2>
            <p className="text-sm text-slate-500">
              {selectedHospital ? bookingLabel(selectedHospital.booking_mode, selectedHospital.booking_confirmation_status) : 'Select a hospital to view specialists'}
            </p>
          </div>
        </div>

        {doctorError && (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-700">
            {doctorError}
          </div>
        )}

        {doctorLoading ? (
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : doctors.length === 0 ? (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
            <Stethoscope className="mx-auto text-slate-400" size={36} />
            <h3 className="mt-3 text-base font-black text-slate-800">Doctors will appear here</h3>
            <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-slate-500">
              Select a hospital to compare specialists and available consultation types.
            </p>
          </div>
        ) : (
          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            {doctors.map((doctor) => (
              <article key={doctor.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg">
                <div className="flex items-start gap-3">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                    <Stethoscope size={22} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate text-base font-black text-slate-950">{doctor.name}</h3>
                    <p className="text-sm font-semibold text-blue-700">{doctor.specialization}</p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <div className="rounded-2xl bg-slate-50 p-3">
                    <div className="text-xs font-bold text-slate-400">Experience</div>
                    <div className="font-black text-slate-800">{doctor.experience_years}+ yrs</div>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-3">
                    <div className="text-xs font-bold text-slate-400">Rating</div>
                    <div className="inline-flex items-center gap-1 font-black text-slate-800">
                      <Star size={14} className="fill-amber-400 text-amber-400" /> {doctor.rating || 'New'}
                    </div>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(doctor.consultation_types || ['in-person']).map((type) => {
                    const Icon = TYPE_ICONS[type] || MapPin;
                    return (
                      <span key={type} className="inline-flex items-center gap-1 rounded-full bg-slate-50 px-2.5 py-1 text-xs font-bold text-slate-600">
                        <Icon size={13} /> {type}
                      </span>
                    );
                  })}
                </div>
                <div className="mt-3 space-y-2 text-sm text-slate-500">
                  <p className="flex items-center gap-2"><Clock size={15} /> {(doctor.available_timings || []).join(', ') || 'Slots available'}</p>
                  {doctor.consultation_fee && (
                    <p className="flex items-center gap-2"><DollarSign size={15} /> Consultation fee: {doctor.consultation_fee}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => openBooking(doctor)}
                  className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-700 px-4 py-3 text-sm font-black text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-800"
                >
                  <CalendarCheck size={16} />
                  Book Appointment
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-base font-black text-slate-950">
              <History size={18} />
              Appointment History
            </h2>
            <p className="text-sm text-slate-500">Upcoming, completed, cancelled, and fallback confirmations.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {FILTERS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setFilter(item.key)}
                className={`rounded-2xl px-3 py-2 text-sm font-black transition ${
                  filter === item.key ? 'bg-blue-700 text-white shadow-lg shadow-blue-700/20' : 'border border-slate-200 bg-white text-slate-600 hover:bg-blue-50 hover:text-blue-700'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {historyLoading ? (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : visibleAppointments.length === 0 ? (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
            <CalendarCheck className="mx-auto text-slate-400" size={36} />
            <h3 className="mt-3 text-base font-black text-slate-800">No appointments in this view</h3>
            <p className="mt-1 text-sm text-slate-500">Your booked consultations will show up here with confirmation status.</p>
          </div>
        ) : (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {visibleAppointments.map((appointment) => {
              const meta = STATUS_META[appointment.status] || STATUS_META.scheduled;
              const TypeIcon = TYPE_ICONS[appointment.consultation_type] || MapPin;
              return (
                <article key={appointment.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-lg">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-2xl bg-blue-50 px-3 py-2 text-center">
                        <div className="text-xl font-black text-blue-700">{new Date(`${appointment.appointment_date}T00:00:00`).getDate()}</div>
                        <div className="text-xs font-black uppercase text-blue-500">
                          {new Date(`${appointment.appointment_date}T00:00:00`).toLocaleDateString('en-US', { month: 'short' })}
                        </div>
                      </div>
                      <div>
                        <h3 className="font-black text-slate-950">{appointment.doctor_name}</h3>
                        <p className="text-sm font-semibold text-blue-700">{appointment.doctor_specialty || 'Specialist'}</p>
                      </div>
                    </div>
                    <span className={`rounded-full border px-2.5 py-1 text-xs font-black ${meta.tone}`}>{meta.label}</span>
                  </div>
                  <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
                    <p className="flex items-center gap-2"><Building2 size={15} /> {appointment.hospital_name}</p>
                    <p className="flex items-center gap-2"><Clock size={15} /> {formatDate(appointment.appointment_date)} at {formatTime(appointment.appointment_time)}</p>
                    <p className="flex items-center gap-2"><TypeIcon size={15} /> {appointment.consultation_type}</p>
                    <p className="flex items-center gap-2"><BellRing size={15} /> {bookingLabel(appointment.booking_mode, appointment.booking_confirmation_status)}</p>
                  </div>
                  {(appointment.appointment_reason || appointment.symptoms_notes || appointment.notes) && (
                    <p className="mt-3 rounded-2xl bg-slate-50 p-3 text-sm leading-6 text-slate-600">
                      {appointment.appointment_reason || appointment.symptoms_notes || appointment.notes}
                    </p>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {!['cancelled', 'completed'].includes(appointment.status) && (
                      <>
                        <button
                          type="button"
                          onClick={() => openReschedule(appointment)}
                          className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-black text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                        >
                          <RefreshCw size={15} /> Reschedule
                        </button>
                        <button
                          type="button"
                          onClick={() => cancelAppointment(appointment)}
                          className="inline-flex items-center gap-2 rounded-2xl border border-rose-200 bg-white px-3 py-2 text-sm font-black text-rose-700 transition hover:bg-rose-50"
                        >
                          <X size={15} /> Cancel
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      onClick={() => quickRebook(appointment)}
                      className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-3 py-2 text-sm font-black text-white transition hover:bg-blue-800"
                    >
                      <CalendarCheck size={15} /> Quick Rebook
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {modalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm" onClick={closeModal}>
          <div className="max-h-full w-full max-w-3xl overflow-y-auto rounded-3xl bg-white shadow-2xl" onClick={(event) => event.stopPropagation()}>
            <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-100 bg-white p-5">
              <div>
                <h2 className="text-xl font-black text-slate-950">{modalTitle}</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {activeDoctor?.name || activeDoctor?.doctor_name} · {selectedHospital?.name || activeDoctor?.hospital_name}
                </p>
              </div>
              <button
                type="button"
                onClick={closeModal}
                className="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 text-slate-500 transition hover:bg-slate-50"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid gap-5 p-5 lg:grid-cols-5">
              <div className="lg:col-span-2">
                <div className="rounded-3xl border border-blue-100 bg-blue-50 p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-blue-700">
                      <Stethoscope size={20} />
                    </div>
                    <div>
                      <div className="font-black text-slate-950">{activeDoctor?.name || activeDoctor?.doctor_name}</div>
                      <div className="text-sm font-semibold text-blue-700">
                        {activeDoctor?.specialization || activeDoctor?.doctor_specialty}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2 text-sm text-slate-600">
                    <p className="flex items-center gap-2"><Building2 size={15} /> {selectedHospital?.name || activeDoctor?.hospital_name}</p>
                    <p className="flex items-center gap-2"><ActiveTypeIcon size={15} /> {bookingForm.consultation_type}</p>
                    <p className="flex items-center gap-2"><BellRing size={15} /> Reminder 1 hour before</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4 lg:col-span-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="block">
                    <span className="text-sm font-bold text-slate-700">Date</span>
                    <input
                      type="date"
                      min={localDateInput()}
                      value={bookingForm.appointment_date}
                      onChange={(event) => setBookingForm((prev) => ({ ...prev, appointment_date: event.target.value }))}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    />
                  </label>
                  <label className="block">
                    <span className="text-sm font-bold text-slate-700">Consultation Type</span>
                    <select
                      value={bookingForm.consultation_type}
                      onChange={(event) => setBookingForm((prev) => ({ ...prev, consultation_type: event.target.value }))}
                      className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    >
                      {(bookingDoctor?.consultation_types || ['in-person', 'video', 'phone']).map((type) => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </label>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-700">Available Slots</span>
                    {slotsLoading && <span className="inline-flex items-center gap-1 text-xs font-bold text-blue-700"><Loader2 size={13} className="auth-spinner" /> Loading</span>}
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {slots.length === 0 && !slotsLoading ? (
                      <div className="col-span-full rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-center text-sm font-semibold text-slate-500">
                        No slots available for this date.
                      </div>
                    ) : slots.map((slot) => {
                      const value = String(slot.time).slice(0, 5);
                      return (
                        <button
                          key={value}
                          type="button"
                          disabled={!slot.available}
                          onClick={() => setBookingForm((prev) => ({ ...prev, appointment_time: value }))}
                          className={`rounded-2xl border px-3 py-3 text-sm font-black transition ${
                            bookingForm.appointment_time === value
                              ? 'border-blue-700 bg-blue-700 text-white shadow-lg shadow-blue-700/20'
                              : slot.available
                                ? 'border-slate-200 bg-white text-slate-700 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700'
                                : 'cursor-not-allowed border-slate-100 bg-slate-50 text-slate-300'
                          }`}
                          title={!slot.available ? slot.unavailable_reason || 'Unavailable' : ''}
                        >
                          {formatTime(value)}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {!rescheduleTarget && (
                  <>
                    <label className="block">
                      <span className="text-sm font-bold text-slate-700">Appointment Reason</span>
                      <input
                        value={bookingForm.appointment_reason}
                        onChange={(event) => setBookingForm((prev) => ({ ...prev, appointment_reason: event.target.value }))}
                        className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                        placeholder="Consultation, follow-up, screening..."
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-bold text-slate-700">Symptoms / Notes</span>
                      <textarea
                        rows={3}
                        value={bookingForm.symptoms_notes}
                        onChange={(event) => setBookingForm((prev) => ({ ...prev, symptoms_notes: event.target.value }))}
                        className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                        placeholder="Symptoms, diagnosis context, medications, allergies..."
                      />
                    </label>
                  </>
                )}

                <label className="block">
                  <span className="text-sm font-bold text-slate-700">Follow-up Details</span>
                  <textarea
                    rows={2}
                    value={bookingForm.follow_up_details}
                    onChange={(event) => setBookingForm((prev) => ({ ...prev, follow_up_details: event.target.value }))}
                    className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    placeholder="Previous visit, report ID, or follow-up request..."
                  />
                </label>

                <button
                  type="button"
                  disabled={!bookingForm.appointment_date || !bookingForm.appointment_time || saving}
                  onClick={rescheduleTarget ? confirmReschedule : confirmBooking}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-700 px-4 py-3 text-sm font-black text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving ? <Loader2 size={16} className="auth-spinner" /> : <CalendarCheck size={16} />}
                  {rescheduleTarget ? 'Save New Slot' : 'Confirm Appointment'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
