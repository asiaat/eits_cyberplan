import { useEffect, useState } from "react"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { ImrSummaryStatistics } from "@/lib/imr-types"

export type StatsFilter = {
  type: "priority" | "pearo_status"
  value: string
} | null

interface ImrDashboardStatsProps {
  activeFilter?: StatsFilter
  onFilterChange?: (filter: StatsFilter) => void
}

const STATUS_ORDER = ["P", "E", "A", "R", "O", "U"] as const

const PEARO_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  P: { bg: "bg-slate-100 dark:bg-slate-800", text: "text-slate-700 dark:text-slate-300", border: "border-slate-200 dark:border-slate-700" },
  E: { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-300", border: "border-amber-200 dark:border-amber-800" },
  A: { bg: "bg-orange-100 dark:bg-orange-950", text: "text-orange-700 dark:text-orange-300", border: "border-orange-200 dark:border-orange-800" },
  R: { bg: "bg-emerald-100 dark:bg-emerald-950", text: "text-emerald-700 dark:text-emerald-300", border: "border-emerald-200 dark:border-emerald-800" },
  O: { bg: "bg-blue-100 dark:bg-blue-950", text: "text-blue-700 dark:text-blue-300", border: "border-blue-200 dark:border-blue-800" },
  U: { bg: "bg-gray-100 dark:bg-gray-800", text: "text-gray-700 dark:text-gray-300", border: "border-gray-200 dark:border-gray-700" },
}

const PRIORITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  P1: { bg: "bg-red-100 dark:bg-red-950", text: "text-red-700 dark:text-red-300", border: "border-red-200 dark:border-red-800" },
  P2: { bg: "bg-orange-100 dark:bg-orange-950", text: "text-orange-700 dark:text-orange-300", border: "border-orange-200 dark:border-orange-800" },
  P3: { bg: "bg-blue-100 dark:bg-blue-950", text: "text-blue-700 dark:text-blue-300", border: "border-blue-200 dark:border-blue-800" },
}

function isActive(filter: StatsFilter | undefined, type: "priority" | "pearo_status", value: string): boolean {
  return filter?.type === type && filter?.value === value
}

export function ImrDashboardStats({ activeFilter, onFilterChange }: ImrDashboardStatsProps) {
  const { t } = useTranslation()
  const { loading, error, getImrSummary } = useImrApi()
  const [stats, setStats] = useState<ImrSummaryStatistics | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    const data = await getImrSummary()
    setStats(data)
  }

  const handleClick = (type: "priority" | "pearo_status", value: string) => {
    if (!onFilterChange) return
    if (isActive(activeFilter, type, value)) {
      onFilterChange(null)
    } else {
      onFilterChange({ type, value })
    }
  }

  if (loading) {
    return <div className="text-center py-4">{t("common.loading")}</div>
  }

  if (error || !stats) {
    return <div className="text-red-600 py-4">{t("common.info")}</div>
  }

  const total = stats.total_items || 1

  const pct = (n: number) => Math.round((n / total) * 100)

  return (
    <div className="space-y-2 mb-3">
      {/* Row 1: Priorities (bigger) */}
      <div className="grid grid-cols-3 gap-2">
        {(["P1", "P2", "P3"] as const).map((code) => {
          const count = stats.priority_counts[code] || 0
          const colors = PRIORITY_COLORS[code]
          const active = isActive(activeFilter, "priority", code)
          return (
            <button
              key={code}
              type="button"
              onClick={() => handleClick("priority", code)}
              className={`bg-card rounded-lg border p-4 flex flex-col items-center text-center transition-all cursor-pointer ${
                active
                  ? `${colors.border} ring-2 ring-indigo-500`
                  : `${colors.border} hover:ring-2 hover:ring-indigo-300`
              }`}
            >
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                {t(`implementationPlan.priority.${code}` as any)}
              </div>
              <div className={`text-5xl font-bold ${colors.text}`}>
                {count}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {pct(count)}%
              </div>
            </button>
          )
        })}
      </div>

      {/* Row 2: Statuses PEARO + U (smaller) */}
      <div className="grid grid-cols-6 gap-2">
        {STATUS_ORDER.map((code) => {
          const count = stats.pearo_status_counts[code] || 0
          const colors = PEARO_COLORS[code]
          const active = isActive(activeFilter, "pearo_status", code)
          return (
            <button
              key={code}
              type="button"
              onClick={() => handleClick("pearo_status", code)}
              className={`bg-card rounded-lg border p-2 flex flex-col items-center text-center transition-all cursor-pointer ${
                active
                  ? `${colors.border} ring-2 ring-indigo-500`
                  : `${colors.border} hover:ring-2 hover:ring-indigo-300`
              }`}
            >
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-0.5">
                {code} — {t(`implementationPlan.status.${code}` as any)}
              </div>
              <div className={`text-xl font-bold ${colors.text}`}>
                {count}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {pct(count)}%
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
