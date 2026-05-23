import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL || "/api/v2"

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  const tenantId = localStorage.getItem("current_org_id") || localStorage.getItem("tenant_id")

  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`
  }
  if (tenantId) {
    config.headers["X-Tenant-ID"] = tenantId
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)

// Asset Relations API
export const assetRelationsApi = {
  listRelations: (assetId: string) =>
    apiClient.get(`/assets/${assetId}/relations`),

  createRelation: (assetId: string, data: {
    target_asset_id: string
    relation_type_code: string
    description?: string
    bidirectional?: boolean
    strength?: string
  }) =>
    apiClient.post(`/assets/${assetId}/relations`, data),

  deleteRelation: (assetId: string, relationId: string) =>
    apiClient.delete(`/assets/${assetId}/relations/${relationId}`),

  getProtectionInheritance: (assetId: string) =>
    apiClient.get(`/assets/${assetId}/protection-inheritance`),

  listRelationTypes: () =>
    apiClient.get(`/assets/relation-types`),
}