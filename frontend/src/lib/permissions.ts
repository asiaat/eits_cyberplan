export function hasRole(requiredRole: string): boolean {
  const userRole = localStorage.getItem("user_role")
  if (!userRole) return false
  if (requiredRole === "admin") {
    return userRole === "admin"
  }
  return userRole === "admin" || userRole === "ism" || userRole === requiredRole
}

export function canEdit(): boolean {
  return hasRole("admin") || hasRole("ism")
}

export function canManageUsers(): boolean {
  return hasRole("admin")
}

export function canImportCatalog(): boolean {
  return hasRole("admin")
}

export function canManageRisks(): boolean {
  return hasRole("admin") || hasRole("ism")
}

export function canUploadEvidence(): boolean {
  return hasRole("admin") || hasRole("ism") || hasRole("process_owner") || hasRole("asset_owner")
}