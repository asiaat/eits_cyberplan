import { useState, useRef, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAlerts } from "@/contexts/AlertContext"
import { useTranslation } from "@/lib/i18n"
import { Bell, Info, AlertTriangle, XCircle, CheckCircle, X, Check } from "lucide-react"
import { cn } from "@/lib/utils"

const levelConfig = {
  info: { icon: Info, color: "text-blue-500", bg: "bg-blue-500" },
  warning: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500" },
  error: { icon: XCircle, color: "text-red-500", bg: "bg-red-500" },
  success: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500" },
}

const badgeColors = {
  error: "bg-red-500",
  warning: "bg-yellow-500",
  info: "bg-blue-500",
  success: "bg-green-500",
  none: "bg-muted",
}

function formatTimeAgo(dateString: string, t: (key: string) => string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t("alerts.justNow")
  if (minutes < 60) return `${minutes} min`
  if (hours < 24) return `${hours} h`
  if (days < 7) return `${days} days`
  return date.toLocaleDateString()
}

export default function AlertBell() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { alerts, markAsRead, markAllAsRead, dismissAlert } = useAlerts()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const activeAlerts = alerts.filter((a: any) => a.is_active !== "false")
  const recentAlerts = activeAlerts.slice(0, 5)
  const unreadAlerts = activeAlerts.filter((a: any) => a.is_read === "false")
  const unreadCount = unreadAlerts.length
  
  const highestPriority = unreadAlerts
    .sort((a: any, b: any) => {
      const priority: Record<string, number> = { error: 0, warning: 1, info: 2, success: 3 }
      return (priority[a.level] || 2) - (priority[b.level] || 2)
    })[0]

  const badgeColor = highestPriority ? badgeColors[highestPriority.level as keyof typeof badgeColors] : badgeColors.none

  const handleAlertClick = (alert: typeof alerts[0]) => {
    if (alert.link) {
      navigate(alert.link)
    }
    if (alert.is_read === "false") {
      markAsRead(alert.id)
    }
    setIsOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-md hover:bg-accent transition-colors"
        title={t("alerts.title")}
      >
        <Bell className="h-5 w-5" />
        <span
          className={cn(
            "absolute -top-1 -right-1 h-5 min-w-5 flex items-center justify-center rounded-full text-xs font-medium text-white",
            badgeColor
          )}
        >
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-md border bg-popover shadow-lg z-50">
          <div className="flex items-center justify-between p-3 border-b">
            <h3 className="font-semibold">{t("alerts.title")}</h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllAsRead()}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                <Check className="h-3 w-3" />
                {t("alerts.markAllRead")}
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {recentAlerts.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground">
                {t("alerts.noAlerts")}
              </div>
            ) : (
              recentAlerts.map((alert) => {
                const config = levelConfig[alert.level]
                const Icon = config.icon

                return (
                  <div
                    key={alert.id}
                    className={cn(
                      "p-3 border-b last:border-b-0 hover:bg-accent cursor-pointer",
                      alert.is_read === "false" && "bg-accent/50"
                    )}
                    onClick={() => handleAlertClick(alert)}
                  >
                    <div className="flex items-start gap-2">
                      <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", config.color)} />
                      <div className="flex-1 min-w-0">
                        <p className={cn("font-medium text-sm", alert.is_read === "false" && "font-semibold")}>
                          {alert.title}
                        </p>
                        {alert.message && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {alert.message}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatTimeAgo(alert.created_at, t)}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          dismissAlert(alert.id)
                        }}
                        className="p-1 hover:bg-muted rounded"
                        title={t("alerts.dismiss")}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>

          {alerts.length > 5 && (
            <div className="p-2 border-t text-center">
              <Link
                to="/alerts"
                onClick={() => setIsOpen(false)}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                {t("alerts.viewAll")}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}