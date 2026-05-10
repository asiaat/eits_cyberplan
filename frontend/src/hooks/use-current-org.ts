import { useState, useEffect, useCallback } from "react"

const CURRENT_ORG_KEY = "current_org_id"

export function useCurrentOrg(userOrganizations: { id: string; name: string }[]) {
  const [currentOrgId, setCurrentOrgId] = useState<string | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem(CURRENT_ORG_KEY)
    if (stored && userOrganizations.some(o => o.id === stored)) {
      setCurrentOrgId(stored)
    } else if (userOrganizations.length > 0) {
      setCurrentOrgId(userOrganizations[0].id)
      localStorage.setItem(CURRENT_ORG_KEY, userOrganizations[0].id)
    }
  }, [userOrganizations])

  const switchOrg = useCallback((orgId: string) => {
    if (userOrganizations.some(o => o.id === orgId)) {
      setCurrentOrgId(orgId)
      localStorage.setItem(CURRENT_ORG_KEY, orgId)
    }
  }, [userOrganizations])

  const currentOrg = userOrganizations.find(o => o.id === currentOrgId) || userOrganizations[0] || null

  return { currentOrgId, currentOrg, switchOrg, organizations: userOrganizations }
}