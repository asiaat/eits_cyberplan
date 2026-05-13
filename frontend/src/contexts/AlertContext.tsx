import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"

const API_BASE = "http://localhost:8000/api/v1"

export interface Alert {
  id: string
  title: string
  message: string | null
  level: "info" | "warning" | "error" | "success"
  target_role: "admin" | "ism" | "all"
  is_read: string
  read_at: string | null
  created_at: string
  link: string | null
  is_active: string
}

interface AlertContextType {
  alerts: Alert[]
  unreadCount: number
  loading: boolean
  fetchAlerts: () => Promise<void>
  fetchHistory: () => Promise<Alert[]>
  markAsRead: (alertId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  dismissAlert: (alertId: string) => Promise<void>
}

const AlertContext = createContext<AlertContextType | undefined>(undefined)

const TOKEN_KEY = "access_token"

function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(TOKEN_KEY)
  }
  return null
}

export function AlertProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAlerts = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const res = await fetch(`${API_BASE}/alerts/`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        setAlerts(data)
      }
    } catch (error) {
      console.error("Failed to fetch alerts:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async (): Promise<Alert[]> => {
    const token = getToken()
    if (!token) return []

    try {
      const res = await fetch(`${API_BASE}/alerts/history`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        return await res.json()
      }
    } catch (error) {
      console.error("Failed to fetch alert history:", error)
    }
    return []
  }, [])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  const markAsRead = useCallback(async (alertId: string) => {
    const token = getToken()
    if (!token) return

    try {
      await fetch(`${API_BASE}/alerts/${alertId}/read`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      })
      setAlerts(prev =>
        prev.map(a =>
          a.id === alertId
            ? { ...a, is_read: "true", read_at: new Date().toISOString() }
            : a
        )
      )
    } catch (error) {
      console.error("Failed to mark alert as read:", error)
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    const token = getToken()
    if (!token) return

    try {
      await fetch(`${API_BASE}/alerts/bulk-read`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      })
      setAlerts(prev =>
        prev.map(a => ({
          ...a,
          is_read: "true",
          read_at: a.read_at || new Date().toISOString(),
        }))
      )
    } catch (error) {
      console.error("Failed to mark all alerts as read:", error)
    }
  }, [])

  const dismissAlert = useCallback(async (alertId: string) => {
    const token = getToken()
    if (!token) return

    try {
      await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })
      setAlerts(prev => prev.filter(a => a.id !== alertId))
    } catch (error) {
      console.error("Failed to dismiss alert:", error)
    }
  }, [])

  const unreadCount = alerts.filter(a => a.is_read === "false").length

  return (
    <AlertContext.Provider
      value={{
        alerts,
        unreadCount,
        loading,
        fetchAlerts,
        fetchHistory,
        markAsRead,
        markAllAsRead,
        dismissAlert,
      }}
    >
      {children}
    </AlertContext.Provider>
  )
}

export function useAlerts() {
  const context = useContext(AlertContext)
  if (!context) {
    throw new Error("useAlerts must be used within an AlertProvider")
  }
  return context
}