import { useState, useEffect, useCallback } from "react"

const TOKEN_KEY = "access_token"
const API_BASE = "http://localhost:8000/api/v1"

export interface UserRole {
  id: string
  code: string
  name: string
}

export interface User {
  id: string
  email: string
  name: string
  is_active: boolean
  roles: UserRole[]
  permissions: string[]
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error("Unauthorized")
      const data = await res.json()
      setUser(data)
      setIsAuthenticated(true)
      localStorage.setItem("user_permissions", JSON.stringify(data.permissions || []))
      localStorage.setItem("user_roles", JSON.stringify(data.roles || []))
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem("user_permissions")
      localStorage.removeItem("user_roles")
    }
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      fetchUser(token).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [fetchUser])

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
    localStorage.setItem("user_permissions", JSON.stringify(userData.permissions || []))
    localStorage.setItem("user_roles", JSON.stringify(userData.roles || []))
  }

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}` },
      })
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem("user_permissions")
      localStorage.removeItem("user_roles")
      setUser(null)
      setIsAuthenticated(false)
    }
  }

  return { user, isAuthenticated, loading, login, logout }
}