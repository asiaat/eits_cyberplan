import { useState, useEffect } from "react"
import { apiClient } from "../lib/api-client"

const TOKEN_KEY = "access_token"
const API_BASE = "http://localhost:8000/api/v1"

export function useAuth() {
  const [user, setUser] = useState<{ id: string; email: string; name: string; is_active: boolean } | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Unauthorized")
          return res.json()
        })
        .then((data) => {
          setUser(data)
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

    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    })

    if (!loginRes.ok) {
      const errorData = await loginRes.json().catch(() => ({}))
      throw new Error(errorData.detail || "Login failed")
    }

    const tokenData = await loginRes.json()
    const token = tokenData.access_token
    localStorage.setItem(TOKEN_KEY, token)

    const userRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!userRes.ok) {
      throw new Error("Failed to get user info")
    }

    const userData = await userRes.json()
    setUser(userData)
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