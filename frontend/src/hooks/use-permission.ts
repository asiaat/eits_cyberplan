import { useCallback } from "react"
import { useAuth } from "@/hooks/use-auth"

export function usePermission() {
  const { user } = useAuth()

  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      if (!user) return false

      const roleCodes = user.roles?.map((r) => r.code) || []
      if (roleCodes.includes("admin")) return true

      if (!user.permissions) return false

      return user.permissions.includes(permissionCode)
    },
    [user]
  )

  const hasAnyPermission = useCallback(
    (permissionCodes: string[]): boolean => {
      if (!user) return false

      const roleCodes = user.roles?.map((r) => r.code) || []
      if (roleCodes.includes("admin")) return true

      if (!user.permissions) return false

      return permissionCodes.some((code) => user.permissions?.includes(code))
    },
    [user]
  )

  const hasAllPermissions = useCallback(
    (permissionCodes: string[]): boolean => {
      if (!user) return false

      const roleCodes = user.roles?.map((r) => r.code) || []
      if (roleCodes.includes("admin")) return true

      if (!user.permissions) return false

      return permissionCodes.every((code) => user.permissions?.includes(code))
    },
    [user]
  )

  const isAdmin = useCallback((): boolean => {
    if (!user) return false
    const roleCodes = user.roles?.map((r) => r.code) || []
    return roleCodes.includes("admin")
  }, [user])

  const isISM = useCallback((): boolean => {
    if (!user) return false
    const roleCodes = user.roles?.map((r) => r.code) || []
    return roleCodes.includes("ism") || roleCodes.includes("admin")
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