import { useState, useEffect } from "react"
import { apiClient } from "../lib/api-client"

const TOKEN_KEY = "access_token"

export function useAuth() {
  const [user, setUser] = useState<{ id: string; email: string; name: string; is_active: boolean } | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      apiClient.get("/auth/me")
        .then((res) => {
          setUser(res.data)
          setIsAuthenticated(true)
        })
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append("username", email)
    formData.append("password", password)
    const res = await apiClient.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
    const token = res.data.access_token
    localStorage.setItem(TOKEN_KEY, token)
    const userRes = await apiClient.get("/auth/me")
    setUser(userRes.data)
    setIsAuthenticated(true)
  }

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout")
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      setUser(null)
      setIsAuthenticated(false)
    }
  }

  return { user, isAuthenticated, loading, login, logout }
}