import { useState, useCallback } from "react"
import { apiClient } from "./api-client"
import { ImrItem, ImrItemUpdate, ImrValidationStatus, ImrSummaryStatistics } from "./imr-types"

export function useImrApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchImrItems = useCallback(async (filters?: {
    pearo_status?: string
    priority?: string
    asset_id?: string
    overdue_only?: boolean
  }): Promise<ImrItem[]> => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters?.pearo_status) params.append("pearo_status", filters.pearo_status)
      if (filters?.priority) params.append("priority", filters.priority)
      if (filters?.asset_id) params.append("asset_id", filters.asset_id)
      if (filters?.overdue_only) params.append("overdue_only", "true")
      
      const response = await apiClient.get(`/imr/?${params.toString()}`)
      return response.data
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch IMR items")
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
      setError(err.response?.data?.detail || "Failed to fetch IMR item")
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
      setError(err.response?.data?.detail || "Failed to update IMR item")
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
      setError(err.response?.data?.detail || "Failed to get validation status")
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
      setError(err.response?.data?.detail || "Failed to link evidence")
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
      setError(err.response?.data?.detail || "Failed to bulk update status")
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
      setError(err.response?.data?.detail || "Failed to fetch IMR summary")
      return null
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
    bulkUpdateStatus,
    getImrSummary,
  }
}