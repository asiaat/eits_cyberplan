import { useCallback } from "react"
import { useAuth } from "@/hooks/use-auth"

export function usePermission() {
  const { user } = useAuth()

  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      if (!user) return false

      const roleNames = user.roles?.map((r) => r.role_name) || []
      if (roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond") || roleNames.includes("superadmin") || roleNames.includes("admin")) return true

      return user.permissions?.includes(permissionCode) || false
    },
    [user]
  )

  const hasAnyPermission = useCallback(
    (permissionCodes: string[]): boolean => {
      if (!user) return false

      const roleNames = user.roles?.map((r) => r.role_name) || []
      if (roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond") || roleNames.includes("superadmin") || roleNames.includes("admin")) return true

      if (!user.permissions) return false

      return permissionCodes.some((code) => user.permissions?.includes(code))
    },
    [user]
  )

  const hasAllPermissions = useCallback(
    (permissionCodes: string[]): boolean => {
      if (!user) return false

      const roleNames = user.roles?.map((r) => r.role_name) || []
      if (roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond") || roleNames.includes("superadmin") || roleNames.includes("admin")) return true

      if (!user.permissions) return false

      return permissionCodes.every((code) => user.permissions?.includes(code))
    },
    [user]
  )

  const isAdmin = useCallback((): boolean => {
    if (!user) return false
    const roleNames = user.roles?.map((r) => r.role_name) || []
    return roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond") || roleNames.includes("superadmin") || roleNames.includes("admin")
  }, [user])

  const isISM = useCallback((): boolean => {
    if (!user) return false
    const roleNames = user.roles?.map((r) => r.role_name) || []
    return roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond") || roleNames.includes("superadmin")
  }, [user])

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
    isISM,
    permissions: user?.permissions || [],
    roles: user?.roles || [],
  }
}