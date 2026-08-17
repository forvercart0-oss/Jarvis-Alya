import { useState, useRef, useEffect } from 'react'
import type { OrbState } from '../../types'
import { Mic, MicOff, Send, Square, Image, X } from 'lucide-react'

interface MessageInputProps {
  onSend: (text: string) => void
  onVoice: () => void
  onStop: () => void
  orbState: OrbState
  streaming: boolean
  micAvailable: boolean
  disabled?: boolean
  onImageSelect?: (file: File) => void
  onImageRemove?: () => void
  attachedImage?: { name: string; size: number; url: string } | null
}

export function MessageInput({
  onSend,
  onVoice,
  onStop,
  orbState,
  streaming,
  micAvailable,
  disabled = false,
  onImageSelect,
  onImageRemove,
  attachedImage,
}: MessageInputProps) {
  const [input, setInput] = useState('')
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (orbState === 'idle' || orbState === 'listening') {
      inputRef.current?.focus()
    }
  }, [orbState])

  useEffect(() => {
    if (attachedImage?.url) {
      setImagePreview(attachedImage.url)
    } else if (!attachedImage) {
      setImagePreview(null)
    }
  }, [attachedImage])

  const submit = () => {
    const text = input.trim()
    if (!text && !imagePreview) return
    onSend(text)
    setInput('')
    setImagePreview(null)
    if (onImageRemove) onImageRemove()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && onImageSelect) {
      onImageSelect(file)
      const reader = new FileReader()
      reader.onload = () => setImagePreview(reader.result as string)
      reader.readAsDataURL(file)
    }
    if (fileRef.current) fileRef.current.value = ''
  }

  const removeImage = () => {
    setImagePreview(null)
    if (onImageRemove) onImageRemove()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
    if (e.key === 'Escape') {
      if (streaming) onStop()
      setInput('')
      removeImage()
    }
  }

  return (
    <div className="px-4 py-3 border-t border-cyan-500/10 flex items-center gap-2">
      <input
        ref={fileRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        onClick={() => fileRef.current?.click()}
        disabled={disabled || streaming}
        className="p-2 rounded-lg bg-slate-800 border border-cyan-500/20 text-cyan-300 hover:bg-cyan-500/10 hover:shadow-[0_0_12px_rgba(0,240,255,0.25)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        title="Attach image"
      >
        <Image className="w-5 h-5" />
      </button>

      {imagePreview && (
        <div className="relative w-10 h-10 rounded border border-cyan-500/30 overflow-hidden">
          <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
          <button
            onClick={removeImage}
            className="absolute -top-1 -right-1 p-0.5 bg-red-500 rounded-full text-white hover:bg-red-400"
            title="Remove image"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={imagePreview ? 'Add a message...' : 'Speak or type a command...'}
        disabled={disabled || streaming}
        className="flex-1 bg-slate-900/80 border border-cyan-500/20 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 focus:shadow-[0_0_12px_rgba(0,240,255,0.15)] transition-all disabled:opacity-50"
      />

      <button
        onClick={onVoice}
        disabled={!micAvailable || disabled || streaming}
        className="p-2 rounded-lg bg-slate-800 border border-cyan-500/20 text-cyan-300 hover:bg-cyan-500/10 hover:shadow-[0_0_12px_rgba(0,240,255,0.25)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        title={micAvailable ? 'Voice input' : 'Microphone unavailable'}
      >
        {orbState === 'listening' ? <MicOff className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
      </button>

      {streaming ? (
        <button
          onClick={onStop}
          className="p-2 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300 hover:bg-red-500/30 transition-all"
          title="Stop generation"
        >
          <Square className="w-5 h-5" />
        </button>
      ) : (
        <button
          onClick={submit}
          disabled={!input.trim() && !imagePreview || disabled}
          className="px-4 py-2 rounded-lg bg-cyan-500/15 border border-cyan-400/40 text-cyan-200 text-sm hover:bg-cyan-400/25 hover:shadow-[0_0_14px_rgba(0,240,255,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}
