import { useAuth } from "@/hooks/use-auth"

export function hasRole(requiredRole: string): boolean {
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  if (!userRoles || userRoles.length === 0) return false

  const roleCodes = userRoles.map((r: { code: string }) => r.code)
  
  if (requiredRole === "admin") {
    return roleCodes.includes("admin")
  }
  
  return roleCodes.includes("admin") || roleCodes.includes("ism") || roleCodes.includes(requiredRole)
}

export function hasPermission(permissionCode: string): boolean {
  const userPermissions = JSON.parse(localStorage.getItem("user_permissions") || "[]")
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  
  if (!userRoles || userRoles.length === 0) return false
  
  const roleCodes = userRoles.map((r: { code: string }) => r.code)
  
  // Admin always has all permissions
  if (roleCodes.includes("admin")) return true
  
  return userPermissions.includes(permissionCode)
}

export function canEdit(): boolean {
  return hasRole("admin") || hasRole("ism")
}

export function canManageUsers(): boolean {
  return hasRole("admin")
}

export function canManageRoles(): boolean {
  return hasRole("admin")
}

export function canImportCatalog(): boolean {
  return hasRole("admin")
}

export function canManageRisks(): boolean {
  return hasRole("admin") || hasRole("ism")
}

export function canUploadEvidence(): boolean {
  return hasPermission("evidence.upload")
}

export function usePermissions() {
  const { user } = useAuth()
  
  const permissions = user?.permissions || []
  const roles = user?.roles?.map(r => r.code) || []
  
  return {
    hasPermission: (code: string) => {
      if (roles.includes("admin")) return true
      return permissions.includes(code)
    },
    hasAnyPermission: (codes: string[]) => {
      if (roles.includes("admin")) return true
      return codes.some(c => permissions.includes(c))
    },
    isAdmin: roles.includes("admin"),
    isISM: roles.includes("ism") || roles.includes("admin"),
    canManageUsers: roles.includes("admin"),
    canManageRoles: roles.includes("admin"),
    canUploadEvidence: permissions.includes("evidence.upload"),
    canManageRisks: roles.includes("admin") || roles.includes("ism"),
  }
}