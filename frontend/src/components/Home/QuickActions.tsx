import { Cpu, HardDrive, Search, Clock, Volume2, Moon, Camera, Terminal } from 'lucide-react'

interface QuickActionsProps {
  onAction: (action: string) => void
}

const ACTIONS = [
  { icon: Cpu, label: 'CPU usage', prompt: 'What is my current CPU usage?' },
  { icon: HardDrive, label: 'Disk space', prompt: 'How much disk space is free?' },
  { icon: Clock, label: 'Date & time', prompt: 'What date and time is it?' },
  { icon: Search, label: 'Web search', prompt: 'Search the web for the latest news' },
  { icon: Volume2, label: 'Set volume', prompt: 'Set the volume to 40 percent' },
  { icon: Moon, label: 'Lock screen', prompt: 'Lock my computer' },
  { icon: Camera, label: 'Screenshot', prompt: 'Take a screenshot' },
  { icon: Terminal, label: 'Open terminal', prompt: 'Open a terminal window' },
]

export function QuickActions({ onAction }: QuickActionsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 px-4 pt-2 -mt-1 [scrollbar-width:none]">
      {ACTIONS.map(({ icon: Icon, label, prompt }) => (
        <button
          key={label}
          onClick={() => onAction(prompt)}
          className="flex items-center gap-1.5 shrink-0 px-2.5 py-1.5 rounded-md glass-panel text-[11px] text-slate-300 hover:text-cyan-300 hover:border-cyan-400/30 transition-all"
        >
          <Icon className="w-3 h-3 text-cyan-400/70" />
          {label}
        </button>
      ))}
    </div>
  )
}
