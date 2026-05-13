import { useState, useEffect, useCallback } from "react"

const TOKEN_KEY = "access_token"
const TENANT_ID_KEY = "tenant_id"
const ORG_ID_KEY = "current_org_id"
const API_BASE = "http://localhost:8000/api/v2"

export interface UserRole {
  id: string
  code: string
  role_name: string
  description?: string
}

export interface User {
  id: string
  email: string
  name: string
  full_name: string
  tenant_id: string
  organizations: string[]
  mfa_enabled: boolean
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
  const [tenantId, setTenantId] = useState<string | null>(null)
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null)

  const fetchUser = useCallback(async (token: string, tenantIdForFetch?: string) => {
    try {
      const tenantIdToUse = tenantIdForFetch || localStorage.getItem(TENANT_ID_KEY) || ""
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantIdToUse,
        },
      })
      if (!res.ok) {
        if (res.status === 401) {
          return null
        }
        throw new Error("Unauthorized")
      }
      const data = await res.json()
      
      const enrichedData = {
        ...data,
        name: data.full_name,
        permissions: data.roles?.map((r: UserRole) => r.role_name) || [],
      }
      
      setUser(enrichedData)
      setIsAuthenticated(true)
      localStorage.setItem("user_email", data.email || "")
      localStorage.setItem("user_full_name", data.full_name || "")
      localStorage.setItem("user_roles", JSON.stringify(data.roles || []))
      return enrichedData
    } catch (error) {
      console.error("fetchUser error:", error)
      return null
    }
  }, [])

  const fetchOrganizations = useCallback(async (token: string, currentTenantId: string) => {
    try {
      const res = await fetch(`${API_BASE}/tenants/my-organizations`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": currentTenantId,
        },
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
    const storedTenantId = localStorage.getItem(TENANT_ID_KEY)
    const storedOrgId = localStorage.getItem(ORG_ID_KEY)
    
    if (token && storedTenantId) {
      setTenantId(storedTenantId)
      setSelectedOrgId(storedOrgId)
      fetchUser(token, storedTenantId).then(() => {
        fetchOrganizations(token, storedTenantId).finally(() => {
          setLoading(false)
        })
      }).catch(() => {
        setLoading(false)
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
    
    localStorage.setItem(TENANT_ID_KEY, userData.tenant_id)
    setTenantId(userData.tenant_id)
    
    const enrichedUserData = {
      ...userData,
      name: userData.full_name,
      permissions: userData.roles?.map((r: UserRole) => r.role_name) || [],
    }
    
    setUser(enrichedUserData)
    setIsAuthenticated(true)
    localStorage.setItem("user_email", userData.email || "")
    localStorage.setItem("user_full_name", userData.full_name || "")
    localStorage.setItem("user_roles", JSON.stringify(userData.roles || []))

    const orgRes = await fetch(`${API_BASE}/tenants/my-organizations`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": userData.tenant_id,
      },
    })
    if (orgRes.ok) {
      const orgs = await orgRes.json()
      setOrganizations(orgs)
      if (orgs.length > 0) {
        localStorage.setItem(ORG_ID_KEY, orgs[0].id)
        setSelectedOrgId(orgs[0].id)
      }
    }
  }

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`,
          "X-Tenant-ID": localStorage.getItem(TENANT_ID_KEY) || "",
        },
      })
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(TENANT_ID_KEY)
      localStorage.removeItem(ORG_ID_KEY)
      localStorage.removeItem("user_email")
      localStorage.removeItem("user_full_name")
      localStorage.removeItem("user_roles")
      setUser(null)
      setIsAuthenticated(false)
      setOrganizations([])
      setTenantId(null)
      setSelectedOrgId(null)
    }
  }

  const selectOrg = useCallback((orgId: string) => {
    localStorage.setItem(ORG_ID_KEY, orgId)
    setSelectedOrgId(orgId)
  }, [])

  const switchTenant = useCallback(async (newTenantId: string) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) return

    localStorage.setItem(TENANT_ID_KEY, newTenantId)
    setTenantId(newTenantId)

    const userRes = await fetch(`${API_BASE}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": newTenantId,
      },
    })
    
    if (userRes.ok) {
      const userData = await userRes.json()
      const enrichedUserData = {
        ...userData,
        name: userData.full_name,
        permissions: userData.roles?.map((r: UserRole) => r.role_name) || [],
      }
      setUser(enrichedUserData)
      localStorage.setItem("user_roles", JSON.stringify(userData.roles || []))
    }

    await fetchOrganizations(token, newTenantId)
  }, [fetchOrganizations])

  return { 
    user, 
    isAuthenticated, 
    loading, 
    login, 
    logout, 
    organizations, 
    tenantId,
    selectedOrgId,
    selectOrg,
    switchTenant 
  }
}