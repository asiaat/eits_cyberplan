import { useAuth } from "@/hooks/use-auth"

export function hasRole(requiredRole: string): boolean {
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  if (!userRoles || userRoles.length === 0) return false

  const roleNames = userRoles.map((r: { role_name: string }) => r.role_name)
  
  if (requiredRole === "superadmin" || requiredRole === "admin") {
    return roleNames.some((n: string) => ["Infoturbejuht", "Juhtkond", "superadmin", "admin"].includes(n))
  }
  
  if (requiredRole === "Infoturbejuht") {
    return roleNames.includes("Infoturbejuht")
  }
  
  if (requiredRole === "IT-talitus") {
    return roleNames.includes("IT-talitus")
  }
  
  if (requiredRole === "Juhtkond") {
    return roleNames.includes("Juhtkond")
  }
  
  return false
}

export function hasPermission(permissionCode: string): boolean {
  const userPermissions = JSON.parse(localStorage.getItem("user_permissions") || "[]")
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  
  if (!userPermissions && !userRoles) return false
  
  const roleNames = userRoles.map((r: { role_name: string }) => r.role_name)
  
  if (roleNames.some((n: string) => ["Infoturbejuht", "Juhtkond", "superadmin", "admin"].includes(n))) {
    return true
  }
  
  return userPermissions.includes(permissionCode)
}

export function canEdit(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond") || hasRole("superadmin")
}

export function canManageUsers(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond") || hasRole("superadmin")
}

export function canManageRoles(): boolean {
  return hasRole("Infoturbejuht") || hasRole("superadmin")
}

export function canImportCatalog(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond") || hasRole("superadmin")
}

export function canManageRisks(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond") || hasRole("superadmin")
}

export function canUploadEvidence(): boolean {
  return hasPermission("evidence.upload")
}

export function usePermissions() {
  const { user } = useAuth()
  
  const roles = user?.roles?.map(r => r.role_name) || []
  const permissions = user?.permissions || []
  
  return {
    hasPermission: (code: string) => {
      if (roles.some(r => ["Infoturbejuht", "Juhtkond", "superadmin", "admin"].includes(r))) return true
      return permissions.includes(code)
    },
    hasAnyPermission: (codes: string[]) => {
      if (roles.some(r => ["Infoturbejuht", "Juhtkond", "superadmin", "admin"].includes(r))) return true
      return codes.some(c => permissions.includes(c))
    },
    hasAllPermissions: (codes: string[]) => {
      if (roles.some(r => ["Infoturbejuht", "Juhtkond", "superadmin", "admin"].includes(r))) return true
      return codes.every(c => permissions.includes(c))
    },
    isAdmin: roles.includes("Infoturbejuht") || roles.includes("Juhtkond") || roles.includes("superadmin") || roles.includes("admin"),
    isISM: roles.includes("Infoturbejuht") || roles.includes("Juhtkond") || roles.includes("superadmin") || roles.includes("ism"),
    canManageUsers: roles.includes("Infoturbejuht") || roles.includes("Juhtkond") || roles.includes("superadmin") || roles.includes("admin"),
    canManageRoles: roles.includes("Infoturbejuht") || roles.includes("superadmin"),
    canUploadEvidence: permissions.includes("evidence.upload"),
    canManageRisks: roles.includes("Infoturbejuht") || roles.includes("Juhtkond") || roles.includes("superadmin"),
    permissions,
    roles,
  }
}