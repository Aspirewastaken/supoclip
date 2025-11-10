"use client"

import * as React from "react"
import { Mic, MicOff, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface VoiceDictationProps {
  onTranscript: (text: string) => void
  onError?: (error: string) => void
  className?: string
  language?: string
  continuous?: boolean
  interimResults?: boolean
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start: () => void
  stop: () => void
  abort: () => void
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null
  onend: ((this: SpeechRecognition, ev: Event) => void) | null
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

export function VoiceDictation({
  onTranscript,
  onError,
  className,
  language = "en-US",
  continuous = false,
  interimResults = true,
}: VoiceDictationProps) {
  const [isListening, setIsListening] = React.useState(false)
  const [isSupported, setIsSupported] = React.useState(true)
  const [interimText, setInterimText] = React.useState("")
  const recognitionRef = React.useRef<SpeechRecognition | null>(null)

  React.useEffect(() => {
    // Check if Web Speech API is supported
    if (typeof window === "undefined") {
      setIsSupported(false)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setIsSupported(false)
      onError?.(
        "Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari."
      )
      return
    }

    // Initialize speech recognition
    const recognition = new SpeechRecognition()
    recognition.continuous = continuous
    recognition.interimResults = interimResults
    recognition.lang = language

    recognition.onstart = () => {
      setIsListening(true)
      setInterimText("")
    }

    recognition.onend = () => {
      setIsListening(false)
      setInterimText("")
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error)
      setIsListening(false)
      setInterimText("")

      let errorMessage = "An error occurred during speech recognition."
      switch (event.error) {
        case "no-speech":
          errorMessage = "No speech was detected. Please try again."
          break
        case "audio-capture":
          errorMessage = "No microphone was found. Please check your microphone settings."
          break
        case "not-allowed":
          errorMessage = "Microphone access was denied. Please allow microphone access."
          break
        case "network":
          errorMessage = "Network error occurred. Please check your internet connection."
          break
        case "aborted":
          errorMessage = "Speech recognition was aborted."
          break
      }

      onError?.(errorMessage)
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ""
      let final = ""

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript

        if (event.results[i].isFinal) {
          final += transcript + " "
        } else {
          interim += transcript
        }
      }

      if (final) {
        onTranscript(final.trim())
        setInterimText("")
      } else if (interim) {
        setInterimText(interim)
      }
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [language, continuous, interimResults, onTranscript, onError])

  const toggleListening = React.useCallback(() => {
    if (!recognitionRef.current) return

    if (isListening) {
      recognitionRef.current.stop()
    } else {
      try {
        recognitionRef.current.start()
      } catch (error) {
        console.error("Failed to start speech recognition:", error)
        onError?.("Failed to start speech recognition. Please try again.")
      }
    }
  }, [isListening, onError])

  if (!isSupported) {
    return (
      <Button
        type="button"
        variant="outline"
        size="icon"
        disabled
        className={cn("relative", className)}
        title="Speech recognition not supported"
      >
        <MicOff className="h-4 w-4 text-muted-foreground" />
      </Button>
    )
  }

  return (
    <div className={cn("relative inline-flex items-center gap-2", className)}>
      <Button
        type="button"
        variant={isListening ? "destructive" : "outline"}
        size="icon"
        onClick={toggleListening}
        className={cn(
          "relative transition-all",
          isListening && "animate-pulse"
        )}
        title={isListening ? "Stop recording" : "Start voice dictation"}
      >
        {isListening ? (
          <Mic className="h-4 w-4" />
        ) : (
          <MicOff className="h-4 w-4" />
        )}

        {isListening && (
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-destructive"></span>
          </span>
        )}
      </Button>

      {interimText && (
        <div className="absolute left-full ml-2 whitespace-nowrap rounded-md bg-muted px-3 py-1.5 text-sm text-muted-foreground shadow-sm">
          {interimText}
          <Loader2 className="inline-block ml-2 h-3 w-3 animate-spin" />
        </div>
      )}
    </div>
  )
}

interface VoiceDictationInputProps extends React.ComponentProps<"input"> {
  onVoiceTranscript?: (text: string) => void
  showVoiceButton?: boolean
  voiceButtonPosition?: "left" | "right"
  language?: string
}

export function VoiceDictationInput({
  onVoiceTranscript,
  showVoiceButton = true,
  voiceButtonPosition = "right",
  language = "en-US",
  className,
  ...props
}: VoiceDictationInputProps) {
  const [value, setValue] = React.useState(props.value || "")
  const [error, setError] = React.useState<string | null>(null)

  const handleTranscript = React.useCallback(
    (text: string) => {
      const newValue = value ? `${value} ${text}` : text
      setValue(newValue)
      onVoiceTranscript?.(newValue)

      // Trigger onChange if it exists
      if (props.onChange) {
        const syntheticEvent = {
          target: { value: newValue },
          currentTarget: { value: newValue },
        } as React.ChangeEvent<HTMLInputElement>
        props.onChange(syntheticEvent)
      }
    },
    [value, onVoiceTranscript, props]
  )

  const handleInputChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setValue(e.target.value)
      props.onChange?.(e)
    },
    [props]
  )

  const handleError = React.useCallback((errorMessage: string) => {
    setError(errorMessage)
    setTimeout(() => setError(null), 5000)
  }, [])

  if (!showVoiceButton) {
    return (
      <input
        {...props}
        value={value}
        onChange={handleInputChange}
        className={className}
      />
    )
  }

  return (
    <div className="relative w-full">
      <div className="relative flex items-center gap-2">
        {voiceButtonPosition === "left" && (
          <VoiceDictation
            onTranscript={handleTranscript}
            onError={handleError}
            language={language}
          />
        )}

        <input
          {...props}
          value={value}
          onChange={handleInputChange}
          className={cn("flex-1", className)}
        />

        {voiceButtonPosition === "right" && (
          <VoiceDictation
            onTranscript={handleTranscript}
            onError={handleError}
            language={language}
          />
        )}
      </div>

      {error && (
        <p className="mt-1.5 text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
