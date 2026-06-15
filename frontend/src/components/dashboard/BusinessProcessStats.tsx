import { useEffect, useState } from "react"
import { useTranslation } from "@/lib/i18n"
import { dashboardApi, DashboardStatsResponse } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ProgressBar } from "@/components/ui/progress"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { FolderKanban } from "lucide-react"

const STATUS_ITEMS = [
  { key: "active", label: "Active", color: "#22c55e" },
  { key: "inactive", label: "Inactive", color: "#6b7280" },
  { key: "archived", label: "Archived", color: "#f97316" },
]

const PROTECTION_COLORS: Record<string, string> = {
  normal: "#3b82f6",
  high: "#f59e0b",
  very_high: "#ef4444",
  unknown: "#9ca3af",
}

const PROTECTION_LABELS: Record<string, string> = {
  normal: "Normal",
  high: "High",
  very_high: "Very High",
  unknown: "Unknown",
}

export default function BusinessProcessStats() {
  const { t } = useTranslation()
  const [stats, setStats] = useState<DashboardStatsResponse["business_processes"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    try {
      const res = await dashboardApi.getStats()
      setStats(res.data.business_processes)
    } catch {
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-4 text-sm text-muted-foreground">{t("common.loading")}</div>
  }

  if (!stats) return null

  const total = stats.total
  const protectionData = Object.entries(stats.by_protection_need)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({ name: PROTECTION_LABELS[key] || key, value: count, color: PROTECTION_COLORS[key] || "#9ca3af" }))

  const assessed = total - (stats.by_protection_need.unknown || 0)
  const assessedPct = total > 0 ? Math.round((assessed / total) * 100) : 0

  const statusItems = STATUS_ITEMS.map((item) => ({
    ...item,
    value: stats.by_status[item.key] || 0,
  }))

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <FolderKanban className="h-5 w-5 text-primary" />
          {t("nav.businessProcesses")}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold">{total}</span>
          <span className="text-sm text-muted-foreground">{t("common.total")}</span>
        </div>

        <div className="flex items-center gap-6">
          <div className="w-28 h-28 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={protectionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={28}
                  outerRadius={44}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {protectionData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1.5 text-sm">
            {protectionData.map((d) => (
              <div key={d.name} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: d.color }} />
                <span className="text-muted-foreground min-w-[5rem]">{d.name}</span>
                <span className="font-medium">{d.value}</span>
              </div>
            ))}
          </div>
        </div>

        <ProgressBar items={statusItems} total={total} />

        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Protection needs assessed</span>
            <span>{assessedPct}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${assessedPct}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
