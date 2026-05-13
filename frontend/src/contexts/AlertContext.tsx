import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"
import { apiClient } from "@/lib/api-client"

export interface Alert {
  id: string
  title: string
  message: string | null
  level: "info" | "warning" | "error" | "success"
  target_role: "admin" | "ism" | "all"
  is_read: boolean
  read_at: string | null
  created_at: string
  link: string | null
  is_active: boolean
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

export function AlertProvider({ children }: { children: ReactNode }) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAlerts = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token")
      const tenantId = localStorage.getItem("tenant_id")
      if (!token || !tenantId) {
        setLoading(false)
        return
      }
      const res = await apiClient.get("/alerts/")
      setAlerts(res.data)
    } catch (error: any) {
      if (error.response?.status !== 401) {
        console.error("Failed to fetch alerts:", error)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async (): Promise<Alert[]> => {
    try {
      const res = await apiClient.get("/alerts/history")
      return res.data
    } catch (error) {
      console.error("Failed to fetch alert history:", error)
    }
    return []
  }, [])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  const markAsRead = useCallback(async (alertId: string) => {
    try {
      await apiClient.post(`/alerts/${alertId}/read`)
      setAlerts(prev =>
        prev.map(a =>
          a.id === alertId
            ? { ...a, is_read: true, read_at: new Date().toISOString() }
            : a
        )
      )
    } catch (error) {
      console.error("Failed to mark alert as read:", error)
    }
  }, [])

  const markAllAsRead = useCallback(async () => {
    try {
      await apiClient.post("/alerts/read-all")
      setAlerts(prev =>
        prev.map(a => ({
          ...a,
          is_read: true,
          read_at: a.read_at || new Date().toISOString(),
        }))
      )
    } catch (error) {
      console.error("Failed to mark all alerts as read:", error)
    }
  }, [])

  const dismissAlert = useCallback(async (alertId: string) => {
    try {
      await apiClient.delete(`/alerts/${alertId}`)
      setAlerts(prev => prev.filter(a => a.id !== alertId))
    } catch (error) {
      console.error("Failed to dismiss alert:", error)
    }
  }, [])

  const unreadCount = alerts.filter(a => !a.is_read).length

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