import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAlerts, Alert } from "@/contexts/AlertContext"
import { useTranslation } from "@/lib/i18n"
import { useAuth } from "@/hooks/use-auth"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Bell, Info, AlertTriangle, XCircle, CheckCircle, X, Check, Archive } from "lucide-react"
import { cn } from "@/lib/utils"

const levelConfig = {
  info: { icon: Info, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/30" },
  warning: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30" },
  error: { icon: XCircle, color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
  success: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500/10", border: "border-green-500/30" },
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

export default function AlertsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { alerts, unreadCount, markAsRead, markAllAsRead, dismissAlert, loading, fetchHistory } = useAlerts()
  const [filter, setFilter] = useState<"all" | "unread">("all")
  const [tab, setTab] = useState<"active" | "history">("active")
  const [historyAlerts, setHistoryAlerts] = useState<Alert[]>([])

  const isAdmin = user?.roles?.some(r => r.code === "admin") || false

  useEffect(() => {
    if (tab === "history" && isAdmin) {
      fetchHistory().then(setHistoryAlerts)
    }
  }, [tab, isAdmin, fetchHistory])

  const activeAlerts = alerts.filter((a: Alert) => a.is_active !== "false")

  const filteredAlerts = filter === "unread"
    ? activeAlerts.filter((a: Alert) => a.is_read === "false")
    : activeAlerts

  const handleAlertClick = (alert: typeof alerts[0]) => {
    if (alert.link) {
      navigate(alert.link)
    }
    if (alert.is_read === "false") {
      markAsRead(alert.id)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="h-8 w-8" />
        <h1 className="text-3xl font-bold">{t("alerts.title")}</h1>
        {unreadCount > 0 && (
          <span className="bg-primary text-primary-foreground px-2 py-0.5 rounded-full text-sm">
            {unreadCount} {t("alerts.unread")}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          <Button
            variant={tab === "active" ? "default" : "outline"}
            onClick={() => setTab("active")}
            size="sm"
          >
            {t("alerts.title")}
          </Button>
          {isAdmin && (
            <Button
              variant={tab === "history" ? "default" : "outline"}
              onClick={() => setTab("history")}
              size="sm"
            >
              <Archive className="h-4 w-4 mr-1" />
              {t("alerts.history")}
            </Button>
          )}
        </div>

        {tab === "active" && (
          <>
            <div className="flex-1" />
            <Button
              variant={filter === "all" ? "default" : "outline"}
              onClick={() => setFilter("all")}
              size="sm"
            >
              {t("alerts.all")}
            </Button>
            <Button
              variant={filter === "unread" ? "default" : "outline"}
              onClick={() => setFilter("unread")}
              size="sm"
            >
              {t("alerts.unreadTab")}
              {unreadCount > 0 && (
                <span className="ml-1 bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded text-xs">
                  {unreadCount}
                </span>
              )}
            </Button>
            {unreadCount > 0 && (
              <Button variant="outline" size="sm" onClick={() => markAllAsRead()}>
                <Check className="h-4 w-4 mr-1" />
                {t("alerts.markAllRead")}
              </Button>
            )}
          </>
        )}
      </div>

      {loading ? (
        <div className="text-center py-8 text-muted-foreground">
          {t("common.loading")}
        </div>
      ) : tab === "history" ? (
        historyAlerts.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              {t("alerts.noHistory")}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {historyAlerts.map((alert) => {
              const config = levelConfig[alert.level as keyof typeof levelConfig]
              const Icon = config.icon
              return (
                <Card key={alert.id} className="opacity-60">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={cn("p-2 rounded-full", config.bg)}>
                        <Icon className={cn("h-5 w-5", config.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium line-through">{alert.title}</h3>
                          <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                            {t("alerts.archived")}
                          </span>
                        </div>
                        {alert.message && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {alert.message}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                          {formatDate(alert.created_at)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )
      ) : filteredAlerts.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {filter === "unread" ? t("alerts.noUnread") : t("alerts.noAlerts")}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => {
            const config = levelConfig[alert.level]
            const Icon = config.icon

            return (
              <Card
                key={alert.id}
                className={cn(
                  "cursor-pointer hover:bg-accent/50 transition-colors",
                  alert.is_read === "false" && "border-l-4",
                  alert.is_read === "false" && config.border
                )}
                onClick={() => handleAlertClick(alert)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={cn("p-2 rounded-full", config.bg)}>
                      <Icon className={cn("h-5 w-5", config.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className={cn("font-medium", alert.is_read === "false" && "font-semibold")}>
                          {alert.title}
                        </h3>
                        {alert.is_read === "false" && (
                          <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded">
                            {t("alerts.new")}
                          </span>
                        )}
                      </div>
                      {alert.message && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {alert.message}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDate(alert.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      {alert.is_read === "false" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            markAsRead(alert.id)
                          }}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          dismissAlert(alert.id)
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}