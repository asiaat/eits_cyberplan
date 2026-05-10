import { useState, useEffect, useCallback } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface OrgInfo {
  id: string
  name: string
}

interface TenantDetails {
  id: string
  name: string
  registry_code: string | null
  legal_form: string | null
  status: string | null
  registered_address: string | null
  contact_address: string | null
  phone: string | null
  email: string | null
  website: string | null
  divisions: { id: string; name: string }[]
}

interface PersonAsset {
  id: string
  name: string
  email: string | null
  description: string | null
  owner_user_id: string | null
  has_user_account: boolean
  user_roles: { id: string; code: string; name: string; is_default?: string }[]
}

interface UserWithRoles {
  id: string
  email: string
  name: string
  is_active: boolean
  roles: { id: string; code: string; name: string; is_default?: string }[]
  linked_asset_id: string | null
}

interface Role {
  id: string
  code: string
  name: string
  description: string | null
  is_default: string
}

export default function OrganizationPage() {
  const { t } = useTranslation()
  const { hasPermission } = usePermission()
  
  const [organizations, setOrganizations] = useState<OrgInfo[]>([])
  const [currentOrgId, setCurrentOrgId] = useState<string | null>(null)
  const [tenant, setTenant] = useState<TenantDetails | null>(null)
  const [people, setPeople] = useState<PersonAsset[]>([])
  const [users, setUsers] = useState<UserWithRoles[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)

  const canManageUsers = hasPermission("users.create")
  const canCreateOrg = hasPermission("organizations.create")
  const canCreatePerson = hasPermission("assets.create")

  // Form states
  const [activeSection, setActiveSection] = useState<"details" | "people" | "users">("details")
  const [orgName, setOrgName] = useState("")
  const [orgRegistryCode, setOrgRegistryCode] = useState("")
  const [newDivisionName, setNewDivisionName] = useState("")
  const [savingOrg, setSavingOrg] = useState(false)

  const [newPersonName, setNewPersonName] = useState("")
  const [newPersonEmail, setNewPersonEmail] = useState("")

  const [newUserName, setNewUserName] = useState("")
  const [newUserEmail, setNewUserEmail] = useState("")
  const [newUserPassword, setNewUserPassword] = useState("")
  const [selectedAssetForUser, setSelectedAssetForUser] = useState("")
  
  const [creatingFromAssetId, setCreatingFromAssetId] = useState<string | null>(null)
  const [newUserPasswordForAsset, setNewUserPasswordForAsset] = useState("")
  const [newUserEmailForAsset, setNewUserEmailForAsset] = useState("")

  // Create org form
  const [showCreateOrg, setShowCreateOrg] = useState(false)
  const [newOrgName, setNewOrgName] = useState("")
  const [newOrgRegistryCode, setNewOrgRegistryCode] = useState("")
  const [newOrgLegalForm, setNewOrgLegalForm] = useState("")
  const [newOrgAddress, setNewOrgAddress] = useState("")
  const [newOrgPhone, setNewOrgPhone] = useState("")
  const [newOrgEmail, setNewOrgEmail] = useState("")
  const [newOrgAdminName, setNewOrgAdminName] = useState("")
  const [newOrgAdminEmail, setNewOrgAdminEmail] = useState("")
  const [newOrgAdminPassword, setNewOrgAdminPassword] = useState("")
  const [creatingOrg, setCreatingOrg] = useState(false)

  const switchOrg = useCallback((orgId: string) => {
    setCurrentOrgId(orgId)
    localStorage.setItem("current_org_id", orgId)
  }, [])

  useEffect(() => {
    loadOrganizations()
  }, [])

  useEffect(() => {
    if (currentOrgId) {
      loadOrgData(currentOrgId)
    }
  }, [currentOrgId])

  const loadOrganizations = async () => {
    try {
      const res = await apiClient.get("/tenants/my-organizations")
      const orgs = res.data
      setOrganizations(orgs)
      
      const stored = localStorage.getItem("current_org_id")
      if (stored && orgs.some((o: OrgInfo) => o.id === stored)) {
        setCurrentOrgId(stored)
      } else if (orgs.length > 0) {
        setCurrentOrgId(orgs[0].id)
        localStorage.setItem("current_org_id", orgs[0].id)
      }
    } catch (error) {
      console.error("Failed to load organizations:", error)
    }
  }

  const loadOrgData = async (orgId: string) => {
    setLoading(true)
    try {
      const [tenantRes] = await Promise.all([
        apiClient.get(`/tenants/${orgId}`),
      ])
      setTenant(tenantRes.data)
      setOrgName(tenantRes.data.name || "")
      setOrgRegistryCode(tenantRes.data.registry_code || "")
      
      // Load people and users for this org
      await loadPeopleAndUsers()
    } catch (error) {
      console.error("Failed to load org data:", error)
    }
    setLoading(false)
  }

  const loadPeopleAndUsers = async (_tenantId?: string) => {
    try {
      const [peopleRes, usersRes, rolesRes] = await Promise.all([
        apiClient.get("/organization/people"),
        apiClient.get("/organization/users"),
        apiClient.get("/roles/"),
      ])
      setPeople(peopleRes.data)
      setUsers(usersRes.data)
      setRoles(rolesRes.data)
    } catch (error) {
      console.error("Failed to load people/users:", error)
    }
  }

  const saveOrgDetails = async () => {
    if (!tenant) return
    setSavingOrg(true)
    try {
      const updated = await apiClient.patch(`/tenants/${tenant.id}`, {
        name: orgName,
        registry_code: orgRegistryCode || null,
        divisions: tenant.divisions || []
      })
      setTenant({ ...tenant, ...updated.data })
    } catch (error: any) {
      console.error("Failed to save:", error)
      alert(error.response?.data?.detail || "Failed to save")
    }
    setSavingOrg(false)
  }

  const addDivision = () => {
    if (!newDivisionName.trim() || !tenant) return
    const newDivision = { id: crypto.randomUUID(), name: newDivisionName.trim() }
    const updatedDivisions = [...(tenant.divisions || []), newDivision]
    setTenant({ ...tenant, divisions: updatedDivisions })
    setNewDivisionName("")
    apiClient.patch(`/tenants/${tenant.id}`, {
      name: orgName,
      registry_code: orgRegistryCode || null,
      divisions: updatedDivisions
    })
  }

  const removeDivision = (divisionId: string) => {
    if (!tenant) return
    const updatedDivisions = (tenant.divisions || []).filter((d: any) => d.id !== divisionId)
    setTenant({ ...tenant, divisions: updatedDivisions })
    apiClient.patch(`/tenants/${tenant.id}`, {
      name: orgName,
      registry_code: orgRegistryCode || null,
      divisions: updatedDivisions
    })
  }

  const createPerson = async () => {
    if (!newPersonName || !tenant) return
    try {
      await apiClient.post("/organization/people", {
        name: newPersonName,
        email: newPersonEmail || null,
        tenant_id: tenant.id
      })
      setNewPersonName("")
      setNewPersonEmail("")
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to create person:", error)
    }
  }

  const createStandaloneUser = async () => {
    if (!newUserName || !newUserEmail || !newUserPassword || !tenant) return
    try {
      await apiClient.post("/organization/users", {
        name: newUserName,
        email: newUserEmail,
        password: newUserPassword,
        tenant_id: tenant.id,
        linked_asset_id: selectedAssetForUser || null,
      })
      setNewUserName("")
      setNewUserEmail("")
      setNewUserPassword("")
      setSelectedAssetForUser("")
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to create user:", error)
    }
  }

  const createUserFromPersonAsset = async (assetId: string) => {
    if (!newUserPasswordForAsset || !tenant) return
    try {
      await apiClient.post(`/organization/people/${assetId}/create-user`, {
        password: newUserPasswordForAsset,
        email: newUserEmailForAsset || null,
      })
      setCreatingFromAssetId(null)
      setNewUserPasswordForAsset("")
      setNewUserEmailForAsset("")
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to create user from asset:", error)
    }
  }

  const assignRole = async (userId: string, roleId: string) => {
    if (!tenant) return
    try {
      await apiClient.post(`/organization/users/${userId}/assign-role`, { role_id: roleId })
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to assign role:", error)
    }
  }

  const removeRole = async (userId: string, roleId: string) => {
    if (!tenant) return
    try {
      await apiClient.delete(`/organization/users/${userId}/remove-role/${roleId}`)
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to remove role:", error)
    }
  }

  const deleteUser = async (userId: string) => {
    if (!confirm("Delete this user?") || !tenant) return
    try {
      await apiClient.delete(`/organization/users/${userId}`)
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to delete user:", error)
    }
  }

  const toggleUserActive = async (userId: string, activate: boolean) => {
    if (!tenant) return
    try {
      const endpoint = activate ? "activate" : "deactivate"
      await apiClient.patch(`/organization/users/${userId}/${endpoint}`)
      loadPeopleAndUsers(tenant.id)
    } catch (error) {
      console.error("Failed to update user status:", error)
    }
  }

  const createOrganization = async () => {
    if (!newOrgName || !newOrgRegistryCode || !newOrgAdminName || !newOrgAdminEmail || !newOrgAdminPassword) return
    setCreatingOrg(true)
    try {
      await apiClient.post("/tenants/", {
        name: newOrgName,
        registry_code: newOrgRegistryCode,
        legal_form: newOrgLegalForm || null,
        registered_address: newOrgAddress || null,
        phone: newOrgPhone || null,
        email: newOrgEmail || null,
        admin_name: newOrgAdminName,
        admin_email: newOrgAdminEmail,
        admin_password: newOrgAdminPassword,
      })
      setShowCreateOrg(false)
      setNewOrgName("")
      setNewOrgRegistryCode("")
      setNewOrgLegalForm("")
      setNewOrgAddress("")
      setNewOrgPhone("")
      setNewOrgEmail("")
      setNewOrgAdminName("")
      setNewOrgAdminEmail("")
      setNewOrgAdminPassword("")
      loadOrganizations()
    } catch (error: any) {
      console.error("Failed to create org:", error)
      alert(error.response?.data?.detail || "Failed to create organization")
    }
    setCreatingOrg(false)
  }

  if (organizations.length === 0 && !loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6">{t("organization.title")}</h1>
        <p className="text-muted-foreground">No organizations found.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("organization.title")}</h1>
      
      {/* Org Selector */}
      <div className="flex items-center gap-4 mb-6 p-4 bg-card border rounded">
        <label className="text-sm font-medium">{t("organization.selectOrg.label") || "Select Organization:"}</label>
        <select 
          className="bg-background text-foreground border-input rounded px-3 py-2 min-w-[200px]"
          value={currentOrgId || ""}
          onChange={(e) => switchOrg(e.target.value)}
        >
          {organizations.map(org => (
            <option key={org.id} value={org.id}>{org.name}</option>
          ))}
        </select>
        {canCreateOrg && (
          <Button variant="outline" size="sm" onClick={() => setShowCreateOrg(true)}>
            + {t("organization.createOrg") || "Create Org"}
          </Button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-8">{t("common.loading")}</div>
      ) : (
        <>
          {/* Section Tabs */}
          <div className="flex gap-2 mb-6">
            <Button variant={activeSection === "details" ? "default" : "outline"} onClick={() => setActiveSection("details")}>
              {t("organization.details") || "Details"}
            </Button>
            <Button variant={activeSection === "people" ? "default" : "outline"} onClick={() => setActiveSection("people")}>
              {t("organization.workersTab")}
            </Button>
            <Button variant={activeSection === "users" ? "default" : "outline"} onClick={() => setActiveSection("users")}>
              {t("organization.cyberplanUsersTab")}
            </Button>
          </div>

          {/* Details Section */}
          {activeSection === "details" && tenant && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{t("organization.details") || "Organization Details"}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t("organization.orgName")}</label>
                      <Input value={orgName} onChange={e => setOrgName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t("organization.registryCode")}</label>
                      <Input value={orgRegistryCode} onChange={e => setOrgRegistryCode(e.target.value)} />
                    </div>
                  </div>
                  <Button onClick={saveOrgDetails} disabled={savingOrg}>
                    {savingOrg ? t("common.saving") : t("common.save")}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Divisions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input 
                      value={newDivisionName}
                      onChange={e => setNewDivisionName(e.target.value)}
                      placeholder="New division name"
                      onKeyDown={e => e.key === "Enter" && addDivision()}
                    />
                    <Button onClick={addDivision}>{t("common.add")}</Button>
                  </div>
                  <div className="space-y-2">
                    {(tenant.divisions || []).map((division: any) => (
                      <div key={division.id} className="flex items-center justify-between p-2 border rounded">
                        <span>{division.name}</span>
                        <Button size="sm" variant="ghost" onClick={() => removeDivision(division.id)} className="text-red-500">
                          {t("common.delete")}
                        </Button>
                      </div>
                    ))}
                    {(tenant.divisions || []).length === 0 && (
                      <p className="text-muted-foreground text-center py-2">No divisions</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* People Section */}
          {activeSection === "people" && tenant && (
            <div className="space-y-4">
              {canCreatePerson && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("organization.addPerson")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2">
                      <Input placeholder={t("organization.personName")} value={newPersonName} onChange={e => setNewPersonName(e.target.value)} />
                      <Input placeholder={t("organization.email")} value={newPersonEmail} onChange={e => setNewPersonEmail(e.target.value)} />
                      <Button onClick={createPerson}>{t("common.add")}</Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>{t("organization.peopleList")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {people.map(person => (
                      <div key={person.id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">{person.name}</div>
                          {person.email && <div className="text-sm text-muted-foreground">{person.email}</div>}
                        </div>
                        <div className="flex items-center gap-2">
                          {person.has_user_account ? (
                            <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
                              {t("organization.hasAccount")}
                              {person.user_roles.length > 0 && (
                                <span className="ml-1">({person.user_roles.map(r => r.name).join(", ")})</span>
                              )}
                            </span>
                          ) : (
                            <>
                              <span className="text-sm bg-yellow-100 text-yellow-800 px-2 py-1 rounded">{t("organization.noAccount")}</span>
                              {canManageUsers && (
                                <Button size="sm" variant="outline" onClick={() => setCreatingFromAssetId(person.id)}>
                                  {t("organization.createUser")}
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                    {people.length === 0 && (
                      <p className="text-muted-foreground text-center py-4">{t("organization.noWorkers")}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {creatingFromAssetId && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                  <Card className="w-96">
                    <CardHeader>
                      <CardTitle>{t("organization.createUserAccount")}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Input placeholder={t("organization.email")} value={newUserEmailForAsset} onChange={e => setNewUserEmailForAsset(e.target.value)} />
                      <Input placeholder={t("organization.password")} type="password" value={newUserPasswordForAsset} onChange={e => setNewUserPasswordForAsset(e.target.value)} />
                      <div className="flex gap-2">
                        <Button onClick={() => createUserFromPersonAsset(creatingFromAssetId)}>{t("common.save")}</Button>
                        <Button variant="outline" onClick={() => setCreatingFromAssetId(null)}>{t("common.cancel")}</Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          )}

          {/* Users Section */}
          {activeSection === "users" && tenant && (
            <div className="space-y-4">
              {canManageUsers && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("organization.addUser")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                      <Input placeholder={t("organization.userName")} value={newUserName} onChange={e => setNewUserName(e.target.value)} />
                      <Input placeholder={t("organization.email")} value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} />
                      <Input placeholder={t("organization.password")} type="password" value={newUserPassword} onChange={e => setNewUserPassword(e.target.value)} />
                      <select className="bg-background text-foreground border-input rounded px-3 py-2" value={selectedAssetForUser} onChange={e => setSelectedAssetForUser(e.target.value)}>
                        <option value="">{t("organization.linkToPerson")}</option>
                        {people.filter(p => !p.has_user_account).map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                    <Button onClick={createStandaloneUser}>{t("common.add")}</Button>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>{t("organization.usersList")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {users.map(user => (
                      <div key={user.id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">
                            {user.name}
                            {!user.is_active && <span className="ml-2 text-xs bg-red-100 text-red-800 px-1 rounded">{t("organization.inactive")}</span>}
                          </div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {user.roles.map(role => (
                            <span key={role.id} className="text-xs bg-secondary px-2 py-1 rounded flex items-center gap-1">
                              {t(`roles.${role.code}.name`)}
                              {canManageUsers && role.is_default !== "true" && (
                                <button onClick={() => removeRole(user.id, role.id)} className="text-red-500">x</button>
                              )}
                            </span>
                          ))}
                          {canManageUsers && (
                            <>
                              <select className="text-xs bg-background text-foreground border-input rounded px-2 py-1" onChange={e => e.target.value && assignRole(user.id, e.target.value)} value="">
                                <option value="">+ {t("organization.addRole")}</option>
                                {roles.filter(r => !user.roles.some(ur => ur.id === r.id)).map(role => (
                                  <option key={role.id} value={role.id}>{t(`roles.${role.code}.name`)}</option>
                                ))}
                              </select>
                              <div className="flex gap-1">
                                {user.is_active ? (
                                  <Button size="sm" variant="outline" onClick={() => toggleUserActive(user.id, false)}>{t("organization.deactivate")}</Button>
                                ) : (
                                  <Button size="sm" variant="outline" onClick={() => toggleUserActive(user.id, true)}>{t("organization.activate")}</Button>
                                )}
                                <Button size="sm" variant="destructive" onClick={() => deleteUser(user.id)}>{t("common.delete")}</Button>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                    {users.length === 0 && (
                      <p className="text-muted-foreground text-center py-4">{t("organization.noUsers")}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}

      {/* Create Org Modal */}
      {showCreateOrg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("organization.createOrg")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("organization.orgName")} *</label>
                  <Input value={newOrgName} onChange={e => setNewOrgName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("organization.registryCode")} *</label>
                  <Input value={newOrgRegistryCode} onChange={e => setNewOrgRegistryCode(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("organization.legalForm")}</label>
                  <Input value={newOrgLegalForm} onChange={e => setNewOrgLegalForm(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("organization.phone")}</label>
                  <Input value={newOrgPhone} onChange={e => setNewOrgPhone(e.target.value)} />
                </div>
                <div className="col-span-2 space-y-2">
                  <label className="text-sm font-medium">{t("organization.address")}</label>
                  <Input value={newOrgAddress} onChange={e => setNewOrgAddress(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("organization.email")}</label>
                  <Input value={newOrgEmail} onChange={e => setNewOrgEmail(e.target.value)} />
                </div>
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-4">Admin User</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t("organization.adminName")} *</label>
                    <Input value={newOrgAdminName} onChange={e => setNewOrgAdminName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t("organization.adminEmail")} *</label>
                    <Input value={newOrgAdminEmail} onChange={e => setNewOrgAdminEmail(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t("organization.adminPassword")} *</label>
                    <Input value={newOrgAdminPassword} onChange={e => setNewOrgAdminPassword(e.target.value)} type="password" />
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button onClick={createOrganization} disabled={creatingOrg}>{creatingOrg ? t("common.saving") : t("common.save")}</Button>
                <Button variant="outline" onClick={() => setShowCreateOrg(false)}>{t("common.cancel")}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}