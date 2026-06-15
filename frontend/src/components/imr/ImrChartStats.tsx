import { useEffect, useState } from "react"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { ImrSummaryStatistics } from "@/lib/imr-types"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { AlertTriangle, CheckCircle2 } from "lucide-react"

const STATUS_ORDER = ["P", "E", "A", "R", "O", "U"] as const

const PEARO_HEX: Record<string, string> = {
  P: "#64748b",
  E: "#d97706",
  A: "#ea580c",
  R: "#059669",
  O: "#2563eb",
  U: "#6b7280",
}

const PRIORITY_HEX: Record<string, string> = {
  P1: "#ef4444",
  P2: "#f97316",
  P3: "#3b82f6",
}

export function ImrChartStats() {
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

  const total = stats.total_items || 1
  const pct = (n: number) => Math.round((n / total) * 100)

  const priorityData = (["P1", "P2", "P3"] as const)
    .filter((code) => (stats.priority_counts[code] || 0) > 0)
    .map((code) => ({
      name: t(`implementationPlan.priority.${code}` as any),
      value: stats.priority_counts[code] || 0,
      color: PRIORITY_HEX[code],
      code,
    }))

  const pearoData = STATUS_ORDER
    .filter((code) => (stats.pearo_status_counts[code] || 0) > 0)
    .map((code) => ({
      name: `${code} — ${t(`implementationPlan.status.${code}` as any)}`,
      value: stats.pearo_status_counts[code] || 0,
      color: PEARO_HEX[code],
      code,
    }))

  const overdueCount = stats.overdue_count || 0
  const readyCount = stats.ready_for_completion_count || 0

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 items-stretch">
        <div className="bg-card rounded-lg border p-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
            {t("dashboard.imr.pearoDistribution")}
          </h3>
          <div className="flex items-center gap-4">
            <div className="w-32 h-32 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pearoData}
                    cx="50%"
                    cy="50%"
                    innerRadius={32}
                    outerRadius={50}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pearoData.map((entry) => (
                      <Cell key={entry.code} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-1.5 text-sm flex-1">
              {pearoData.map((d) => (
                <div key={d.code} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm inline-block shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-muted-foreground min-w-[5rem]">{d.name}</span>
                  <span className="font-medium ml-auto">{d.value}</span>
                  <span className="text-xs text-muted-foreground w-8 text-right">{pct(d.value)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="bg-card rounded-lg border p-4 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium">{t("dashboard.imr.overdue")}</span>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-bold text-destructive">{overdueCount}</span>
              <span className="text-sm text-muted-foreground">/ {total}</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full bg-destructive transition-all duration-500"
                style={{ width: `${pct(overdueCount)}%` }}
              />
            </div>
          </div>

          <div className="bg-card rounded-lg border p-4 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span className="text-sm font-medium">{t("dashboard.imr.readyForCompletion")}</span>
            </div>
            <div className="flex items-baseline gap-2 mb-2">
              <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{readyCount}</span>
              <span className="text-sm text-muted-foreground">/ {total}</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                style={{ width: `${pct(readyCount)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg border p-4">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          {t("dashboard.imr.priorityDistribution")}
        </h3>
        <div className="flex flex-wrap items-center gap-6">
          <div className="w-28 h-28 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={28}
                  outerRadius={44}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {priorityData.map((entry) => (
                    <Cell key={entry.code} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1.5 text-sm">
            {priorityData.map((d) => (
              <div key={d.code} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm inline-block shrink-0" style={{ backgroundColor: d.color }} />
                <span className="text-muted-foreground min-w-[3rem]">{d.name}</span>
                <span className="font-medium">{d.value}</span>
                <span className="text-xs text-muted-foreground">{pct(d.value)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
