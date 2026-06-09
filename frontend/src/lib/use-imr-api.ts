import { useState, useCallback } from "react"
import { apiClient } from "./api-client"
import { ImrItem, ImrItemUpdate, ImrValidationStatus, ImrSummaryStatistics } from "./imr-types"

interface UserOption {
  id: string
  full_name: string
  email: string
  department: string | null
}

function parseError(err: any): string {
  const detail = err?.response?.data?.detail
  if (typeof detail === "string") return detail
  try { return JSON.stringify(detail) } catch { return "An error occurred" }
}

export function useImrApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = useCallback(async (): Promise<UserOption[]> => {
    try {
      const response = await apiClient.get("/users/")
      return response.data || []
    } catch (err: any) {
      console.error("Failed to fetch users", err)
      return []
    }
  }, [])

  const fetchImrItems = useCallback(async (
    filters?: {
      pearo_status?: string
      priority?: string
      asset_id?: string
      overdue_only?: boolean
      module_group?: string
      snapshot_id?: string
      skip?: number
      limit?: number
    }
  ): Promise<ImrItem[]> => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters?.pearo_status) params.append("pearo_status", filters.pearo_status)
      if (filters?.priority) params.append("priority", filters.priority)
      if (filters?.asset_id) params.append("asset_id", filters.asset_id)
      if (filters?.overdue_only) params.append("overdue_only", "true")
      if (filters?.module_group) params.append("module_group", filters.module_group)
      if (filters?.snapshot_id) params.append("snapshot_id", filters.snapshot_id)
      if (filters?.skip) params.append("skip", String(filters.skip))
      if (filters?.limit) params.append("limit", String(filters.limit))
      
      const response = await apiClient.get(`/imr/?${params.toString()}`)
      return response.data
    } catch (err: any) {
      setError(parseError(err) || "Failed to fetch IMR items")
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchImrItem = useCallback(async (itemId: string): Promise<ImrItem | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get(`/imr/${itemId}`)
      return response.data
    } catch (err: any) {
      setError(parseError(err) || "Failed to fetch IMR item")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const updateImrItem = useCallback(async (itemId: string, data: ImrItemUpdate): Promise<ImrItem | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.patch(`/imr/${itemId}`, data)
      return response.data
    } catch (err: any) {
      setError(parseError(err) || "Failed to update IMR item")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const getImrValidationStatus = useCallback(async (itemId: string): Promise<ImrValidationStatus | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get(`/imr/items/${itemId}/validation`)
      return response.data
    } catch (err: any) {
      setError(parseError(err) || "Failed to get validation status")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const linkEvidenceToImr = useCallback(async (itemId: string, evidenceId: string): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await apiClient.post(`/imr/items/${itemId}/evidence?evidence_id=${evidenceId}`)
      return true
    } catch (err: any) {
      setError(parseError(err) || "Failed to link evidence")
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const bulkUpdateItems = useCallback(async (itemIds: string[], updates: Record<string, any>): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await apiClient.patch("/imr/bulk", { item_ids: itemIds, updates })
      return true
    } catch (err: any) {
      setError(parseError(err) || "Failed to bulk update items")
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const bulkUpdateStatus = useCallback(async (itemIds: string[], status: string): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      await apiClient.patch("/imr/bulk-status", { item_ids: itemIds, pearo_status: status })
      return true
    } catch (err: any) {
      setError(parseError(err) || "Failed to bulk update status")
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const getImrSummary = useCallback(async (): Promise<ImrSummaryStatistics | null> => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get("/imr/reports/imr-summary-v2")
      return response.data
    } catch (err: any) {
      setError(parseError(err) || "Failed to fetch IMR summary")
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const exportImrItems = useCallback(async (
    filters?: {
      pearo_status?: string
      priority?: string
      overdue_only?: boolean
    }
  ): Promise<void> => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters?.pearo_status) params.append("pearo_status", filters.pearo_status)
      if (filters?.priority) params.append("priority", filters.priority)
      if (filters?.overdue_only) params.append("overdue_only", "true")

      const response = await apiClient.get(`/imr/export?${params.toString()}`, {
        responseType: "blob",
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement("a")
      link.href = url
      const now = new Date()
      const timestamp = now.toISOString().replace(/[:.]/g, "-").slice(0, 19)
      link.setAttribute("download", `IMR_${timestamp}.xlsx`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(parseError(err) || "Failed to export IMR items")
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    error,
    fetchImrItems,
    fetchImrItem,
    updateImrItem,
    getImrValidationStatus,
    linkEvidenceToImr,
    bulkUpdateItems,
    bulkUpdateStatus,
    getImrSummary,
    exportImrItems,
    fetchUsers,
  }
}