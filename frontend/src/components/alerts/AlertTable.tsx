import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { apiClient } from "@/lib/api-client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Info, AlertTriangle, AlertCircle, CheckCircle, Eye, Trash2 } from "lucide-react"

interface AlertItem {
  id: string
  title: string
  message: string | null
  level: "info" | "warning" | "error" | "success"
  is_read: boolean | string
  created_at: string
  link: string | null
  is_active?: boolean | string
}

type AlertFilter = "current" | "history" | "all"

const LEVEL_CONFIG: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; bg: string }> = {
  info: { icon: Info, color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-950" },
  warning: { icon: AlertTriangle, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-100 dark:bg-amber-950" },
  error: { icon: AlertCircle, color: "text-red-600 dark:text-red-400", bg: "bg-red-100 dark:bg-red-950" },
  success: { icon: CheckCircle, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-950" },
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString()
}

export default function AlertTable() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<AlertFilter>("current")
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
  }, [filter])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      let data: AlertItem[] = []
      if (filter === "current" || filter === "all") {
        const res = await apiClient.get("/dashboard/alerts/current", { params: { limit: 50 } })
        data = [...data, ...res.data.map((a: AlertItem) => ({ ...a, is_active: true }))]
      }
      if (filter === "history" || filter === "all") {
        const res = await apiClient.get("/dashboard/alerts/history", { params: { limit: 100 } })
        const historyData = res.data.map((a: AlertItem) => ({ ...a, is_active: false }))
        const currentIds = new Set(data.map(a => a.id))
        data = filter === "all"
          ? [...data, ...historyData.filter((a: AlertItem) => !currentIds.has(a.id))]
          : historyData
      }
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      setAlerts(data)
    } catch {
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async (alertId: string) => {
    try {
      await apiClient.post(`/alerts/${alertId}/read`)
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a))
    } catch {
      // ignore
    }
  }

  const dismissAlert = async (alertId: string) => {
    try {
      await apiClient.delete(`/alerts/${alertId}`)
      setAlerts(prev => prev.filter(a => a.id !== alertId))
    } catch {
      // ignore
    }
  }

  const markReadTitle = "Mark read"

  const filters: { key: AlertFilter; label: string }[] = [
    { key: "current", label: t("alerts.filterCurrent") },
    { key: "history", label: t("alerts.filterHistory") },
    { key: "all", label: t("alerts.filterAll") },
  ]

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{t("dashboard.alertTableTitle")}</h3>
        <div className="flex gap-1">
          {filters.map(f => (
            <Button
              key={f.key}
              variant={filter === f.key ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </Button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-muted-foreground">{t("common.loading")}</div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">{t("alerts.noAlerts")}</div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground uppercase w-10" />
                <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground uppercase">Title</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground uppercase hidden sm:table-cell">{t("alerts.description")}</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-muted-foreground uppercase w-24">{t("common.time")}</th>
                <th className="text-right px-4 py-2 text-xs font-medium text-muted-foreground uppercase w-24">{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map(alert => {
                const cfg = LEVEL_CONFIG[alert.level] || LEVEL_CONFIG.info
                const Icon = cfg.icon
                const isRead = alert.is_read === true || alert.is_read === "true"
                return (
                  <tr key={alert.id} className={`border-b last:border-0 hover:bg-muted/30 transition-colors ${isRead ? "opacity-60" : ""}`}>
                    <td className="px-4 py-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${cfg.bg}`}>
                        <Icon className={`w-4 h-4 ${cfg.color}`} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className={`text-sm font-medium ${isRead ? "" : ""}`}>{alert.title}</div>
                      {alert.message && (
                        <div className="text-xs text-muted-foreground mt-0.5 sm:hidden">{alert.message}</div>
                      )}
                      <div className="flex gap-2 mt-1">
                        {!isRead && (
                          <Badge variant="default" className="text-[10px] px-1 py-0 h-4">{t("alerts.new")}</Badge>
                        )}
                        {alert.is_active === false && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">{t("alerts.archived")}</Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground hidden sm:table-cell max-w-xs truncate">
                      {alert.message || "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                      {formatTime(alert.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {!isRead && (
                          <button
                            type="button"
                            onClick={() => markAsRead(alert.id)}
                            className="p-1 rounded hover:bg-accent transition-colors"
                            title={markReadTitle}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => dismissAlert(alert.id)}
                          className="p-1 rounded hover:bg-accent transition-colors text-muted-foreground hover:text-red-600"
                          title={t("alerts.dismiss")}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
