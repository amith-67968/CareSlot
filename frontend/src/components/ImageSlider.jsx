import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import healthTechImageOne from '../assets/slider-health-tech-1.webp'
import healthTechImageTwo from '../assets/slider-health-tech-2.jpg'
import healthTechImageThree from '../assets/slider-health-tech-3.webp'
import healthTechImageFour from '../assets/slider-health-tech-4.jpg'

const slides = [
  {
    src: healthTechImageOne,
    alt: 'Doctor using connected healthcare technology',
    label: 'Smart Wellness',
    caption: 'Continuous monitoring for a healthier lifestyle every day.',
  },
  {
    src: healthTechImageTwo,
    alt: 'Doctor interacting with a digital healthcare interface',
    label: 'AI Care Chat',
    caption: 'Ask questions, organize symptoms, and get guided support fast.',
  },
  {
    src: healthTechImageThree,
    alt: 'Clinician using medical AI tools on a laptop',
    label: 'Clinical Insights',
    caption: 'Readable health signals designed for proactive care decisions.',
  },
  {
    src: healthTechImageFour,
    alt: 'Digital medical network with laptop and stethoscope',
    label: 'Care Planning',
    caption: 'Appointments, reminders, and check-ins arranged in one place.',
  },
]

const slideVariants = {
  enter: { opacity: 0, scale: 1.04 },
  center: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.98 },
}

function ImageSlider() {
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % slides.length)
    }, 3800)

    return () => window.clearInterval(interval)
  }, [])

  const activeSlide = slides[activeIndex]

  return (
    <div className="relative w-full">
      <div className="relative aspect-[1.28/1] min-h-[260px] overflow-hidden rounded-3xl bg-slate-200 shadow-2xl shadow-slate-300/80 sm:min-h-[320px] lg:min-h-[380px] xl:min-h-[420px]">
        <AnimatePresence mode="wait">
          <motion.img
            key={activeSlide.src}
            src={activeSlide.src}
            alt={activeSlide.alt}
            className="absolute inset-0 h-full w-full object-cover"
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </AnimatePresence>

        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-slate-950/5 to-white/0" />

        <div className="absolute bottom-7 left-7 right-7 text-white">
          <p className="text-sm font-bold">{activeSlide.label}</p>
          <p className="mt-1 max-w-md text-sm font-medium leading-6 text-white/90">{activeSlide.caption}</p>
        </div>

        <div className="absolute left-6 right-6 top-6 flex gap-2">
          {slides.map((slide, index) => (
            <button
              key={slide.label}
              type="button"
              aria-label={`Go to ${slide.label}`}
              onClick={() => setActiveIndex(index)}
              className="h-1 flex-1 overflow-hidden rounded-full bg-white/35"
            >
              <motion.span
                className="block h-full rounded-full bg-white"
                initial={false}
                animate={{ width: activeIndex === index ? '100%' : '0%' }}
                transition={{ duration: activeIndex === index ? 3.8 : 0.25, ease: 'linear' }}
              />
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-2">
        {slides.map((slide, index) => (
          <button
            key={slide.src}
            type="button"
            aria-label={`Show ${slide.label} slide`}
            aria-current={activeIndex === index}
            onClick={() => setActiveIndex(index)}
            className={`h-3 rounded-full transition-all duration-300 ${
              activeIndex === index ? 'w-3 bg-blue-600 ring-4 ring-blue-100' : 'w-3 bg-slate-300 hover:bg-blue-300'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

export default ImageSlider
