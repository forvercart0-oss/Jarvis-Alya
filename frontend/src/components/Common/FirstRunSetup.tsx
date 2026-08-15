import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, Cpu } from 'lucide-react'
import type { JarvisSettings } from '../../types'

interface FirstRunSetupProps {
  settings: JarvisSettings | null
  onComplete: () => void
  onUpdate: (patch: Partial<JarvisSettings>) => void
}

type Step = 'welcome' | 'name' | 'ai' | 'voice' | 'finish'

export function FirstRunSetup({ settings, onComplete, onUpdate }: FirstRunSetupProps) {
  const [step, setStep] = useState<Step>('welcome')
  const [name, setName] = useState(settings?.assistant_name || 'JARVIS')
  const [userName, setUserName] = useState(settings?.user_name || 'Sir')
  const [provider, setProvider] = useState<'groq' | 'local'>('groq')
  const [apiKey, setApiKey] = useState('')
  const [localUrl, setLocalUrl] = useState('')
  const [localModel, setLocalModel] = useState('')

  const steps: Step[] = ['welcome', 'name', 'ai', 'voice', 'finish']
  const currentIndex = steps.indexOf(step)

  const handleNext = () => {
    const next = steps[currentIndex + 1]
    if (next) setStep(next)
    else onComplete()
  }

  const handleSkip = () => {
    const next = steps[currentIndex + 1]
    if (next) setStep(next)
    else onComplete()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative w-full max-w-lg glass-panel shadow-2xl"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-cyan-500/10">
          <h2 className="text-sm tracking-[0.2em] text-cyan-400/70 uppercase">Initial Setup</h2>
          <span className="text-[10px] text-slate-600">Step {currentIndex + 1} / {steps.length}</span>
        </div>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 'welcome' && (
              <motion.div key="welcome" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg text-cyan-400 mb-2">Welcome to JARVIS 2.0</h3>
                <p className="text-sm text-slate-400 mb-6">
                  Let&apos;s configure your personal desktop assistant. This will only take a minute.
                </p>
                <div className="flex justify-end">
                  <button onClick={handleNext} className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Get Started
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'name' && (
              <motion.div key="name" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg text-cyan-400 mb-4">Personalize JARVIS</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Assistant Name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">How should I address you?</label>
                    <input
                      type="text"
                      value={userName}
                      onChange={(e) => setUserName(e.target.value)}
                      className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400/60"
                    />
                  </div>
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={handleSkip} className="px-4 py-2 text-xs text-slate-500 hover:text-slate-300 transition-colors">Skip</button>
                  <button onClick={() => { onUpdate({ assistant_name: name, user_name: userName }); handleNext(); }} className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Next
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'ai' && (
              <motion.div key="ai" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg text-cyan-400 mb-4">Choose AI Provider</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => setProvider('groq')}
                    className={`w-full p-4 rounded-lg border text-left transition-all ${provider === 'groq' ? 'border-cyan-400/60 bg-cyan-500/10' : 'border-slate-600/30 bg-slate-800/50 hover:border-cyan-400/30'}`}
                  >
                    <div className="flex items-center gap-3">
                      <Cpu className="w-5 h-5 text-cyan-400" />
                      <div>
                        <div className="text-sm text-slate-200">Groq Cloud</div>
                        <div className="text-[10px] text-slate-500">Fast cloud inference - requires API key</div>
                      </div>
                    </div>
                  </button>
                  <button
                    onClick={() => setProvider('local')}
                    className={`w-full p-4 rounded-lg border text-left transition-all ${provider === 'local' ? 'border-cyan-400/60 bg-cyan-500/10' : 'border-slate-600/30 bg-slate-800/50 hover:border-cyan-400/30'}`}
                  >
                    <div className="flex items-center gap-3">
                      <Cpu className="w-5 h-5 text-cyan-400" />
                      <div>
                        <div className="text-sm text-slate-200">Local LLM</div>
                        <div className="text-[10px] text-slate-500">Run on your own server</div>
                      </div>
                    </div>
                  </button>
                </div>

                {provider === 'groq' && (
                  <div className="mt-4">
                    <label className="block text-xs text-slate-400 mb-1">Groq API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="gsk_..."
                      className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 font-mono"
                    />
                  </div>
                )}

                {provider === 'local' && (
                  <div className="mt-4 space-y-3">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Server URL</label>
                      <input
                        type="text"
                        value={localUrl}
                        onChange={(e) => setLocalUrl(e.target.value)}
                        placeholder="http://192.168.1.100:11434"
                        className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Model Name</label>
                      <input
                        type="text"
                        value={localModel}
                        onChange={(e) => setLocalModel(e.target.value)}
                        placeholder="llama3"
                        className="w-full bg-slate-900/80 border border-cyan-500/20 rounded px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400/60 font-mono"
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-between mt-6">
                  <button onClick={handleSkip} className="px-4 py-2 text-xs text-slate-500 hover:text-slate-300 transition-colors">Skip</button>
                  <button onClick={() => {
                    if (provider === 'groq') onUpdate({ groq_api_key: apiKey })
                    else onUpdate({ local_llm_enabled: true, local_llm_url: localUrl, local_llm_model: localModel })
                    handleNext()
                  }} className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Next
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'voice' && (
              <motion.div key="voice" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg text-cyan-400 mb-4">Voice Settings</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Mic className="w-8 h-8 text-cyan-400" />
                    <div>
                      <div className="text-sm text-slate-200">Voice Assistant</div>
                      <div className="text-[10px] text-slate-500">Enable microphone and text-to-speech</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">Enable Voice</span>
                    <button
                      onClick={() => onUpdate({ voice_enabled: !settings?.voice_enabled })}
                      className={`w-12 h-6 rounded-full transition-all ${settings?.voice_enabled ? 'bg-cyan-500/40' : 'bg-slate-700'} relative`}
                    >
                      <div className={`absolute top-1 w-4 h-4 rounded-full bg-cyan-400 transition-all ${settings?.voice_enabled ? 'left-7' : 'left-1'}`} />
                    </button>
                  </div>
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={handleSkip} className="px-4 py-2 text-xs text-slate-500 hover:text-slate-300 transition-colors">Skip</button>
                  <button onClick={handleNext} className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Next
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'finish' && (
              <motion.div key="finish" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 className="text-lg text-cyan-400 mb-2">You&apos;re all set!</h3>
                <p className="text-sm text-slate-400 mb-6">
                  JARVIS is ready to assist you. You can change these settings anytime in the Settings panel.
                </p>
                <div className="flex justify-end">
                  <button onClick={onComplete} className="px-4 py-2 bg-cyan-500/15 border border-cyan-400/40 rounded text-xs text-cyan-200 hover:bg-cyan-400/25 transition-all">
                    Launch JARVIS
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}