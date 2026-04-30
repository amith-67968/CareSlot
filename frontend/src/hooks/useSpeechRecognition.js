import { useCallback, useEffect, useRef, useState } from 'react';

function getSpeechRecognition() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function appendTranscript(baseText, transcript) {
  const cleanTranscript = transcript.trim();
  if (!cleanTranscript) return baseText;
  const cleanBase = baseText.replace(/\s+$/, '');
  return cleanBase ? `${cleanBase} ${cleanTranscript}` : cleanTranscript;
}

function getErrorMessage(error) {
  switch (error) {
    case 'not-allowed':
    case 'service-not-allowed':
      return 'Microphone permission was blocked.';
    case 'no-speech':
      return 'No speech detected. Try again.';
    case 'audio-capture':
      return 'No microphone was found.';
    case 'network':
      return 'Speech recognition is unavailable right now.';
    default:
      return 'Voice input stopped unexpectedly.';
  }
}

export default function useSpeechRecognition({ value, onChange, disabled = false }) {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);
  const baseTextRef = useRef('');
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    setIsSupported(Boolean(getSpeechRecognition()));
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      recognitionRef.current = null;
      setIsListening(false);
    }
  }, []);

  const startListening = useCallback(() => {
    if (disabled) return;

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser.');
      return;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        recognitionRef.current = null;
      }
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    baseTextRef.current = valueRef.current;
    setError('');

    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      if (recognitionRef.current !== recognition) return;
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      if (recognitionRef.current !== recognition) return;

      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = 0; i < event.results.length; i += 1) {
        const transcript = event.results[i][0]?.transcript || '';
        if (event.results[i].isFinal) {
          finalTranscript += `${transcript} `;
        } else {
          interimTranscript += `${transcript} `;
        }
      }

      onChangeRef.current(
        appendTranscript(baseTextRef.current, `${finalTranscript}${interimTranscript}`),
      );
    };

    recognition.onerror = (event) => {
      if (recognitionRef.current !== recognition) return;
      setError(getErrorMessage(event.error));
    };

    recognition.onend = () => {
      if (recognitionRef.current !== recognition) return;
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognition.start();
  }, [disabled]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
      return;
    }
    startListening();
  }, [isListening, startListening, stopListening]);

  useEffect(() => {
    if (disabled && isListening) {
      stopListening();
    }
  }, [disabled, isListening, stopListening]);

  useEffect(() => () => {
    recognitionRef.current?.abort();
  }, []);

  return {
    clearError: () => setError(''),
    error,
    isListening,
    isSupported,
    startListening,
    stopListening,
    toggleListening,
  };
}
