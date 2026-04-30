/**
 * CareSlot — Landing Page
 * Extracted from the original App.jsx.
 */

import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ChevronRight, HeartPulse, Sparkles } from 'lucide-react';
import ImageSlider from '../components/ImageSlider';

export default function Landing() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const primaryPath = user ? '/dashboard' : '/auth';

  return (
    <main className="h-screen overflow-hidden bg-[#f5f8ff] text-[#06122f]">
      <header className="border-b border-blue-100/80 bg-white/90 shadow-sm shadow-blue-100/60 backdrop-blur-xl">
        <nav className="flex w-full items-center justify-between py-4 pl-0 pr-4 sm:pr-6 lg:pr-8">
          <a href="/" className="flex items-center gap-2" aria-label="CareSlot home">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-600/25">
              <HeartPulse size={18} strokeWidth={2.4} />
            </span>
            <span className="text-lg font-bold tracking-tight text-blue-700">CareSlot</span>
          </a>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(primaryPath)}
              className="hidden text-sm font-medium text-slate-600 transition hover:text-blue-700 sm:inline-flex"
            >
              {user ? 'Dashboard' : 'Login'}
            </button>
            <button
              onClick={() => navigate(primaryPath)}
              className="rounded-xl bg-blue-700 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-800"
            >
              {user ? 'Open Dashboard' : 'Get Started'}
            </button>
          </div>
        </nav>
      </header>

      <section id="home" className="relative">
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,#f7faff_0%,#f3f7ff_55%,#eef5ff_100%)]" />

        <div className="grid h-[calc(100vh-73px)] w-full items-start gap-8 px-0 pb-8 pt-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-6 lg:pr-0 lg:pb-8 lg:pt-16">
          <div className="max-w-2xl pl-6 sm:pl-8 lg:pl-10">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm">
              <Sparkles size={15} />
              Next-Gen Medical Intelligence
            </div>

            <h1 className="animate-headline-fade-in max-w-3xl font-['Playfair_Display'] text-4xl font-semibold leading-[1.06] tracking-tight text-slate-950 sm:text-[2.85rem] lg:text-[3.25rem] xl:text-[3.65rem]">
              <span className="block whitespace-nowrap">Detect, Consult, and Cure</span>
              <span className="block whitespace-nowrap font-bold text-blue-700">Powered by AI</span>
            </h1>

            <p className="mt-10 max-w-[34rem] text-base leading-7 text-slate-600">
              Experience proactive healthcare that understands you. From instant disease screening to real-time posture analysis, we bridge the gap between clinical excellence and daily life.
            </p>

            <div className="mt-7 flex flex-col gap-4 sm:flex-row">
              <button
                onClick={() => navigate(primaryPath)}
                className="inline-flex items-center justify-center rounded-xl bg-blue-700 px-8 py-4 text-sm font-bold text-white shadow-xl shadow-blue-700/20 transition hover:-translate-y-1 hover:bg-blue-800"
              >
                {user ? 'Open Dashboard' : 'Get Started'}
              </button>
              <a
                href="#footer"
                className="inline-flex items-center justify-center rounded-xl border-2 border-teal-600 bg-white/60 px-8 py-4 text-sm font-bold text-teal-700 transition hover:-translate-y-1 hover:bg-teal-50"
              >
                Learn More
              </a>
            </div>
          </div>

          <div className="relative w-full max-w-[760px] justify-self-end pr-5 lg:pl-0 lg:pr-10">
            <div className="absolute -inset-y-5 left-4 right-0 -z-10 rounded-l-[2rem] bg-white/60 blur-2xl" />
            <ImageSlider />
          </div>
        </div>
      </section>

      <footer id="footer" className="hidden border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-slate-500 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-blue-600 text-white">
              <HeartPulse size={20} />
            </span>
            <span className="font-bold text-slate-950">CareSlot</span>
          </div>
          <div className="flex flex-wrap gap-5">
            <a className="transition hover:text-blue-600" href="#home">
              Back to top
              <ChevronRight className="inline" size={14} />
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}
