import { useEffect, useState } from "react"
import { useTranslation } from "@/lib/i18n"
import { dashboardApi, DashboardStatsResponse } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ProgressBar } from "@/components/ui/progress"
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import { Boxes } from "lucide-react"

const TYPE_COLORS: Record<string, string> = {
  information_asset: "#6366f1",
  software: "#0ea5e9",
  hardware: "#14b8a6",
  service: "#8b5cf6",
  data: "#f43f5e",
  competence: "#06b6d4",
  other: "#6b7280",
}

const CRITICALITY_ITEMS = [
  { key: "low", color: "#6b7280" },
  { key: "normal", color: "#3b82f6" },
  { key: "high", color: "#f59e0b" },
  { key: "critical", color: "#ef4444" },
]

export default function AssetStats() {
  const { t } = useTranslation()
  const [stats, setStats] = useState<DashboardStatsResponse["assets"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    try {
      const res = await dashboardApi.getStats()
      setStats(res.data.assets)
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
  const typeData = Object.entries(stats.by_type)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({ name: t(`assets.types.${key}` as any), value: count, color: TYPE_COLORS[key] || "#9ca3af" }))

  const criticalityItems = CRITICALITY_ITEMS.map((item) => ({
    ...item,
    label: t(`assets.criticalityLevels.${item.key}` as any),
    value: stats.by_criticality[item.key] || 0,
  }))

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Boxes className="h-5 w-5 text-primary" />
          {t("nav.assets")}
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
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={28}
                  outerRadius={44}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {typeData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1.5 text-sm">
            {typeData.map((d) => (
              <div key={d.name} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: d.color }} />
                <span className="text-muted-foreground min-w-[5rem]">{d.name}</span>
                <span className="font-medium">{d.value}</span>
              </div>
            ))}
          </div>
        </div>

        <ProgressBar items={criticalityItems} total={total} />
      </CardContent>
    </Card>
  )
}
