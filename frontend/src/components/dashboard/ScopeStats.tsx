import { useEffect, useState } from "react"
import { useTranslation } from "@/lib/i18n"
import { dashboardApi, DashboardStatsResponse } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield } from "lucide-react"

const APPROACH_COLORS: Record<string, { bg: string; text: string; bar: string; label: string }> = {
  BASIC: { bg: "bg-blue-100 dark:bg-blue-950", text: "text-blue-700 dark:text-blue-300", bar: "bg-blue-500", label: "BASIC" },
  STANDARD: { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-300", bar: "bg-amber-500", label: "STANDARD" },
  CORE: { bg: "bg-purple-100 dark:bg-purple-950", text: "text-purple-700 dark:text-purple-300", bar: "bg-purple-500", label: "CORE" },
}

const APPROACH_LEVELS = ["BASIC", "STANDARD", "CORE"]

export default function ScopeStats() {
  const { t } = useTranslation()
  const [stats, setStats] = useState<DashboardStatsResponse["scope"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    try {
      const res = await dashboardApi.getStats()
      setStats(res.data.scope)
    } catch {
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-4 text-sm text-muted-foreground">{t("common.loading")}</div>
  }

  if (!stats) return null

  const approach = stats.active_approach
  const colors = approach ? APPROACH_COLORS[approach] : null
  const currentLevel = approach ? APPROACH_LEVELS.indexOf(approach) + 1 : 0

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          {t("protectionmode.title")}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        {approach ? (
          <>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold ${colors?.bg} ${colors?.text}`}>
                {t(`protectionmode.approaches.${approach.toLowerCase()}.name` as any)}
              </span>
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{approach}</span>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{t("protectionmode.level")}</span>
                <span>{currentLevel} / 3</span>
              </div>
              <div className="flex gap-1 h-2">
                {APPROACH_LEVELS.map((level, idx) => (
                  <div
                    key={level}
                    className={`flex-1 rounded-full transition-all duration-500 ${
                      idx < currentLevel ? colors?.bar : "bg-muted"
                    }`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>BASIC</span>
                <span>STANDARD</span>
                <span>CORE</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-muted rounded-lg p-4 text-center">
                <div className="text-3xl font-bold">{stats.modules_count}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wide mt-1">
                  {t("catalog.tabs.modules")}
                </div>
              </div>
              <div className="bg-muted rounded-lg p-4 text-center">
                <div className="text-3xl font-bold">{stats.measures_count}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wide mt-1">
                  {t("catalog.tabs.measures")}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="py-6 text-center text-sm text-muted-foreground">
            <Shield className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p>{t("common.none")}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
