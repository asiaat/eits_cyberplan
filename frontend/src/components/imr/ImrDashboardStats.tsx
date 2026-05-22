import { useEffect, useState } from "react"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { ImrSummaryStatistics } from "@/lib/imr-types"
import { IMR_STATUS_OPTIONS } from "@/lib/imr-types"

export function ImrDashboardStats() {
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

  if (loading) {
    return <div className="text-center py-4">{t("common.loading")}</div>
  }

  if (error || !stats) {
    return <div className="text-red-600 py-4">{t("common.info")}</div>
  }

  const statusColors: Record<string, string> = {
    P: "bg-muted text-foreground",
    E: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300",
    A: "bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300",
    R: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300",
    O: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300",
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
      {/* Total Items */}
      <div className="bg-card rounded-lg border border-border p-3">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          {t("implementationPlan.dashboard.totalItems")}
        </div>
        <div className="text-2xl font-bold text-foreground mt-1">
          {stats.total_items}
        </div>
      </div>

      {/* Overdue */}
      <div className="bg-card rounded-lg border border-border p-3">
        <div className="text-xs font-semibold text-red-600 uppercase tracking-wide">
          {t("implementationPlan.dashboard.overdue")}
        </div>
        <div className="text-2xl font-bold text-red-600 mt-1">
          {stats.overdue_count}
        </div>
      </div>

      {/* Implemented */}
      <div className="bg-card rounded-lg border border-border p-3">
        <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">
          {t("implementationPlan.dashboard.implemented")}
        </div>
        <div className="text-2xl font-bold text-emerald-600 mt-1">
          {stats.pearo_status_counts["R"] || 0}
        </div>
      </div>

      {/* In Progress */}
      <div className="bg-card rounded-lg border border-border p-3">
        <div className="text-xs font-semibold text-amber-600 uppercase tracking-wide">
          {t("implementationPlan.dashboard.inProgress")}
        </div>
        <div className="text-2xl font-bold text-amber-600 mt-1">
          {stats.pearo_status_counts["E"] || 0}
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="col-span-2 md:col-span-4 bg-white rounded-lg border border-slate-200 p-3">
        <div className="flex flex-wrap gap-2">
          {IMR_STATUS_OPTIONS.map((option) => {
            const count = stats.pearo_status_counts[option.value] || 0
            
            return (
              <div 
                key={option.value}
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${statusColors[option.value]}`}
              >
                <span className="font-bold">{option.value}</span>
                <span className="font-medium">{t(`implementationPlan.status.${option.value}` as any)}</span>
                <span className="text-xs opacity-75">({count})</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}