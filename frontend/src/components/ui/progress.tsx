import { cn } from "@/lib/utils"

interface ProgressProps {
  value: number
  max?: number
  className?: string
  barClassName?: string
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
  label?: string
  color?: string
}

const sizeClasses = {
  sm: "h-1.5",
  md: "h-2.5",
  lg: "h-4",
}

export function Progress({
  value,
  max = 100,
  className,
  barClassName,
  size = "md",
  showLabel = false,
  label,
  color,
}: ProgressProps) {
  const pct = Math.min(Math.round((value / max) * 100), 100)

  return (
    <div className={cn("space-y-1", className)}>
      {showLabel && (
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{label}</span>
          <span>{pct}%</span>
        </div>
      )}
      <div className={cn("w-full bg-muted rounded-full overflow-hidden", sizeClasses[size])}>
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            sizeClasses[size],
            color || "bg-primary",
            barClassName
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

interface ProgressBarProps {
  items: { key: string; label: string; value: number; color: string }[]
  total: number
  className?: string
}

export function ProgressBar({ items, total, className }: ProgressBarProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex h-3 w-full bg-muted rounded-full overflow-hidden">
        {items.map((item) => {
          const pct = total > 0 ? (item.value / total) * 100 : 0
          if (pct <= 0) return null
          return (
            <div
              key={item.key}
              className="h-full transition-all duration-500"
              style={{ width: `${pct}%`, backgroundColor: item.color }}
              title={`${item.label}: ${item.value} (${Math.round(pct)}%)`}
            />
          )
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {items.map((item) => (
          <div key={item.key} className="flex items-center gap-1 text-xs text-muted-foreground">
            <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: item.color }} />
            <span>{item.label}</span>
            <span className="font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
