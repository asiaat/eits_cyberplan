import { useState, useEffect, useCallback } from "react"

const TOKEN_KEY = "access_token"
const ORG_ID_KEY = "current_org_id"
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

export interface Organization {
  id: string
  name: string
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null)

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

  const fetchOrganizations = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/tenants/my-organizations`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const orgs = await res.json()
        setOrganizations(orgs)
        return orgs
      }
    } catch (error) {
      console.error("Failed to fetch organizations:", error)
    }
    return []
  }, [])

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      fetchUser(token).then(() => {
        fetchOrganizations(token).then((orgs) => {
          const storedOrgId = localStorage.getItem(ORG_ID_KEY)
          if (storedOrgId && orgs.some((o: Organization) => o.id === storedOrgId)) {
            setSelectedOrgId(storedOrgId)
          }
          setLoading(false)
        })
      })
    } else {
      setLoading(false)
    }
  }, [fetchUser, fetchOrganizations])

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

    const orgs = await fetchOrganizations(token)
    if (orgs.length > 0) {
      if (orgs.length === 1) {
        localStorage.setItem(ORG_ID_KEY, orgs[0].id)
        setSelectedOrgId(orgs[0].id)
      }
    }
  }

  const selectOrg = useCallback((orgId: string) => {
    localStorage.setItem(ORG_ID_KEY, orgId)
    setSelectedOrgId(orgId)
  }, [])

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}` },
      })
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(ORG_ID_KEY)
      localStorage.removeItem("user_permissions")
      localStorage.removeItem("user_roles")
      setUser(null)
      setIsAuthenticated(false)
      setOrganizations([])
      setSelectedOrgId(null)
    }
  }

  return { user, isAuthenticated, loading, login, logout, organizations, selectedOrgId, selectOrg }
}