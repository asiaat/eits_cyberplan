import { useAuth } from "@/hooks/use-auth"

export function hasRole(requiredRole: string): boolean {
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  if (!userRoles || userRoles.length === 0) return false

  const roleNames = userRoles.map((r: { role_name: string }) => r.role_name)
  
  if (requiredRole === "admin" || requiredRole === "Juhtkond") {
    return roleNames.includes("Juhtkond") || roleNames.includes("Infoturbejuht")
  }
  
  return roleNames.includes("Juhtkond") || roleNames.includes("Infoturbejuht") || roleNames.includes("IT-talitus")
}

export function hasPermission(permissionCode: string): boolean {
  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")
  
  if (!userRoles || userRoles.length === 0) return false
  
  const roleNames = userRoles.map((r: { role_name: string }) => r.role_name)
  
  if (roleNames.includes("Infoturbejuht") || roleNames.includes("Juhtkond")) return true
  
  const rolePermissions: Record<string, string[]> = {
    "IT-talitus": ["evidence.upload", "assets.manage"],
  }
  
  for (const role of roleNames) {
    if (rolePermissions[role]?.includes(permissionCode)) return true
  }
  
  return false
}

export function canEdit(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond")
}

export function canManageUsers(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond")
}

export function canManageRoles(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond")
}

export function canImportCatalog(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond")
}

export function canManageRisks(): boolean {
  return hasRole("Infoturbejuht") || hasRole("Juhtkond")
}

export function canUploadEvidence(): boolean {
  return hasPermission("evidence.upload")
}

export function usePermissions() {
  const { user } = useAuth()
  
  const roles = user?.roles?.map(r => r.role_name) || []
  
  return {
    hasPermission: (_code: string) => {
      if (roles.includes("Infoturbejuht") || roles.includes("Juhtkond")) return true
      return false
    },
    hasAnyPermission: (_codes: string[]) => {
      if (roles.includes("Infoturbejuht") || roles.includes("Juhtkond")) return true
      return false
    },
    isAdmin: roles.includes("Infoturbejuht") || roles.includes("Juhtkond"),
    isISM: roles.includes("Infoturbejuht") || roles.includes("Juhtkond"),
    canManageUsers: roles.includes("Infoturbejuht") || roles.includes("Juhtkond"),
    canManageRoles: roles.includes("Infoturbejuht") || roles.includes("Juhtkond"),
    canUploadEvidence: hasPermission("evidence.upload"),
    canManageRisks: roles.includes("Infoturbejuht") || roles.includes("Juhtkond"),
  }
}