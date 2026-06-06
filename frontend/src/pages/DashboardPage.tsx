import { useEffect, useState } from "react"
import { useTranslation } from "@/lib/i18n"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ImrDashboardStats } from "@/components/imr/ImrDashboardStats"
import AlertTable from "@/components/alerts/AlertTable"
import { CheckCircle, Clock, AlertTriangle, FileText, Shield, TrendingUp, ListChecks } from "lucide-react"

interface DashboardSummary {
  total_imr_items: number
  implemented_items: number
  in_progress_items: number
  not_started_items: number
  overdue_items: number
  high_risks: number
  items_without_evidence: number
  imr_completion_percentage: number
  audit_readiness_score: number
}

interface HeatmapRow {
  protection_need: string
  normal: number
  high: number
  very_high: number
  unknown: number
}

interface RiskHeatmap {
  protection_needs: string[]
  risk_levels: string[]
  data: HeatmapRow[]
  total_business_processes: number
}

const PROTECTION_NEED_LABELS: Record<string, string> = {
  normal: "protectionNeed.normal",
  high: "protectionNeed.high",
  very_high: "protectionNeed.very_high",
  unknown: "protectionNeed.unknown",
}

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "risks.low",
  medium: "risks.medium",
  high: "risks.high",
  very_high: "risks.veryHigh",
}

function getHeatmapColor(val: number, max: number): string {
  if (max === 0) return "bg-muted"
  const ratio = val / max
  if (ratio === 0) return "bg-muted"
  if (ratio <= 0.25) return "bg-emerald-200 dark:bg-emerald-800"
  if (ratio <= 0.5) return "bg-amber-200 dark:bg-amber-800"
  if (ratio <= 0.75) return "bg-orange-200 dark:bg-orange-800"
  return "bg-red-200 dark:bg-red-800"
}

function getScoreColor(score: number): string {
  if (score >= 70) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 40) return "text-amber-600 dark:text-amber-400"
  return "text-red-600 dark:text-red-400"
}

function getScoreBg(score: number): string {
  if (score >= 70) return "bg-emerald-100 dark:bg-emerald-950 border-emerald-200 dark:border-emerald-800"
  if (score >= 40) return "bg-amber-100 dark:bg-amber-950 border-amber-200 dark:border-amber-800"
  return "bg-red-100 dark:bg-red-950 border-red-200 dark:border-red-800"
}

export default function DashboardPage() {
  const { t } = useTranslation()
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [heatmap, setHeatmap] = useState<RiskHeatmap | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [summaryRes, heatmapRes] = await Promise.all([
        apiClient.get("/dashboard/summary"),
        apiClient.get("/dashboard/risk-heatmap"),
      ])
      setSummary(summaryRes.data)
      setHeatmap(heatmapRes.data)
    } catch {
      setSummary(null)
      setHeatmap(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">{t("dashboard.title")}</h1>
        <div className="text-center py-12 text-muted-foreground">{t("common.loading")}</div>
      </div>
    )
  }

  const stats = summary
    ? [
        { label: t("dashboard.totalMeasures"), value: summary.total_imr_items, icon: ListChecks, color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-950" },
        { label: t("dashboard.implemented"), value: summary.implemented_items, icon: CheckCircle, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-950" },
        { label: t("dashboard.inProgress"), value: summary.in_progress_items, icon: Clock, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-100 dark:bg-amber-950" },
        { label: t("dashboard.overdue"), value: summary.overdue_items, icon: AlertTriangle, color: "text-red-600 dark:text-red-400", bg: "bg-red-100 dark:bg-red-950" },
        { label: t("dashboard.highRisks"), value: summary.high_risks, icon: Shield, color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-100 dark:bg-orange-950" },
        { label: t("dashboard.measuresWithoutEvidence"), value: summary.items_without_evidence, icon: FileText, color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-100 dark:bg-purple-950" },
      ]
    : []

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">{t("dashboard.title")}</h1>

      {/* Summary stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {stats.map(stat => {
          const Icon = stat.icon
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">{stat.label}</CardTitle>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stat.bg}`}>
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* IMR Progress & Audit Readiness */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* IMR Progress */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  {t("dashboard.imrProgress")}
                </CardTitle>
                {summary && (
                  <Badge variant="outline" className="text-sm">
                    {summary.imr_completion_percentage}% {t("dashboard.completionPercentage")}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <ImrDashboardStats />
            </CardContent>
          </Card>
        </div>

        {/* Audit Readiness Score */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="w-5 h-5 text-primary" />
                {t("dashboard.auditReadiness")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary ? (
                <div className="flex flex-col items-center py-4">
                  <div className={`text-6xl font-bold mb-2 ${getScoreColor(summary.audit_readiness_score)}`}>
                    {summary.audit_readiness_score}
                  </div>
                  <div className="text-sm text-muted-foreground mb-4">{t("dashboard.score")}</div>
                  <div className={`w-full rounded-full h-3 ${getScoreBg(summary.audit_readiness_score)} border`}>
                    <div
                      className={`h-full rounded-full transition-all ${getScoreColor(summary.audit_readiness_score).replace("text-", "bg-").replace("dark:text-", "dark:bg-")}`}
                      style={{ width: `${Math.min(summary.audit_readiness_score, 100)}%` }}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4 w-full mt-6 text-center">
                    <div>
                      <div className="text-2xl font-bold">{summary.total_imr_items}</div>
                      <div className="text-xs text-muted-foreground">{t("dashboard.totalMeasures")}</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{summary.implemented_items}</div>
                      <div className="text-xs text-muted-foreground">{t("dashboard.implemented")}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">{t("dashboard.noData")}</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Risk Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-primary" />
            {t("dashboard.riskHeatmap")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {heatmap && heatmap.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[400px]">
                <thead>
                  <tr>
                    <th className="text-left px-3 py-2 text-xs font-medium text-muted-foreground" />
                    {heatmap.risk_levels.map(rl => (
                      <th key={rl} className="px-3 py-2 text-xs font-medium text-muted-foreground text-center">
                        {t(RISK_LEVEL_LABELS[rl] || rl)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {heatmap.data.map(row => {
                    const values = heatmap.risk_levels.map(rl => (row as any)[rl] || 0)
                    const maxVal = Math.max(...values, 1)
                    return (
                      <tr key={row.protection_need}>
                        <td className="px-3 py-2 text-sm font-medium">
                          {t(PROTECTION_NEED_LABELS[row.protection_need] || row.protection_need)}
                        </td>
                        {values.map((val: number, i: number) => (
                          <td key={i} className="px-3 py-2 text-center">
                            <div className={`rounded-lg px-3 py-2 ${getHeatmapColor(val, maxVal)}`}>
                              <span className="text-sm font-semibold">{val}</span>
                            </div>
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <div className="text-xs text-muted-foreground mt-2">
                {t("common.total")}: {heatmap.total_business_processes} {t("businessProcesses.title").toLowerCase()}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">{t("dashboard.noData")}</div>
          )}
        </CardContent>
      </Card>

      {/* Alert table */}
      <AlertTable />
    </div>
  )
}
