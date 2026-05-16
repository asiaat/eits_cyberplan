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

  console.log("API Request:", config.method?.toUpperCase(), config.url, "token:", token ? "yes" : "NO", "tenant:", tenantId)
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error("API Error:", error.response?.status, error.config?.url, error.response?.data)
    return Promise.reject(error)
  }
)