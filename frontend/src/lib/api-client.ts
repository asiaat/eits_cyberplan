import axios from "axios"

export const apiClient = axios.create({
  baseURL: "/api/v2",
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