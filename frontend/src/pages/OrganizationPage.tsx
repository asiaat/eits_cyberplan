import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

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
  const { hasPermission, hasAnyPermission } = usePermission()
  
  const [activeTab, setActiveTab] = useState("company")
  const [people, setPeople] = useState<PersonAsset[]>([])
  const [users, setUsers] = useState<UserWithRoles[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)

  // Company state
  const [company, setCompany] = useState<any>(null)
  const [companyEditing, setCompanyEditing] = useState(false)
  const [companyForm, setCompanyForm] = useState<any>({})

  // Division state
  const [divisions, setDivisions] = useState<any[]>([])
  // const [divisionTree, setDivisionTree] = useState<any[]>([])
  const [divisionModalOpen, setDivisionModalOpen] = useState(false)
  const [editingDivision, setEditingDivision] = useState<any>(null)
  const [divisionForm, setDivisionForm] = useState({ code: "", name: "", description: "", parent_division_id: "", head_user_id: "" })
  
  // Form states
  const [newPersonName, setNewPersonName] = useState("")
  const [newPersonEmail, setNewPersonEmail] = useState("")
  const [newUserName, setNewUserName] = useState("")
  const [newUserEmail, setNewUserEmail] = useState("")
  const [newUserPassword, setNewUserPassword] = useState("")
  const [selectedAssetForUser, setSelectedAssetForUser] = useState("")
  
  // User create from asset modal
  const [creatingFromAssetId, setCreatingFromAssetId] = useState<string | null>(null)
  const [newUserPasswordForAsset, setNewUserPasswordForAsset] = useState("")
  const [newUserEmailForAsset, setNewUserEmailForAsset] = useState("")

  const canViewPeople = hasAnyPermission(["processes.view", "assets.view", "dashboard.view"])
  const canManageUsers = hasPermission("users.create")
  const canManageOrg = hasPermission("organization.edit")
  const canManagePeople = hasPermission("people.manage")
  const canManageDivisions = hasPermission("organization.edit")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [companyRes, divisionsRes, peopleRes, usersRes, rolesRes] = await Promise.all([
        apiClient.get("/organization/company"),
        apiClient.get("/organization/divisions"),
        apiClient.get("/organization/people"),
        apiClient.get("/organization/users"),
        apiClient.get("/roles/"),
      ])
      setCompany(companyRes.data)
      setCompanyForm(companyRes.data)
      setDivisions(divisionsRes.data)
      setPeople(peopleRes.data)
      setUsers(usersRes.data)
      setRoles(rolesRes.data)
    } catch (error) {
      console.error("Failed to load organization data:", error)
    }
    setLoading(false)
  }

  const saveCompany = async () => {
    try {
      const res = await apiClient.patch("/organization/company", companyForm)
      setCompany(res.data)
      setCompanyForm(res.data)
      setCompanyEditing(false)
    } catch (error) {
      console.error("Failed to save company:", error)
    }
  }

  const saveDivision = async () => {
    if (!divisionForm.code || !divisionForm.name) return
    try {
      if (editingDivision) {
        await apiClient.patch(`/organization/divisions/${editingDivision.id}`, divisionForm)
      } else {
        await apiClient.post("/organization/divisions", divisionForm)
      }
      setDivisionModalOpen(false)
      loadData()
    } catch (error) {
      console.error("Failed to save division:", error)
    }
  }

  const deleteDivision = async (id: string) => {
    if (!confirm(t("organization.confirmDeleteDivision"))) return
    try {
      await apiClient.delete(`/organization/divisions/${id}`)
      loadData()
    } catch (error) {
      console.error("Failed to delete division:", error)
    }
  }

  const createPerson = async () => {
    if (!newPersonName) return
    try {
      await apiClient.post("/organization/people", {
        name: newPersonName,
        email: newPersonEmail || null,
      })
      setNewPersonName("")
      setNewPersonEmail("")
      loadData()
    } catch (error) {
      console.error("Failed to create person:", error)
    }
  }

  const createUserFromPersonAsset = async (assetId: string) => {
    if (!newUserPasswordForAsset) return
    try {
      await apiClient.post(`/organization/people/${assetId}/create-user`, {
        password: newUserPasswordForAsset,
        email: newUserEmailForAsset || null,
      })
      setCreatingFromAssetId(null)
      setNewUserPasswordForAsset("")
      setNewUserEmailForAsset("")
      loadData()
    } catch (error) {
      console.error("Failed to create user from asset:", error)
    }
  }

  const createStandaloneUser = async () => {
    if (!newUserName || !newUserEmail || !newUserPassword) return
    try {
      await apiClient.post("/organization/users", {
        name: newUserName,
        email: newUserEmail,
        password: newUserPassword,
        linked_asset_id: selectedAssetForUser || null,
      })
      setNewUserName("")
      setNewUserEmail("")
      setNewUserPassword("")
      setSelectedAssetForUser("")
      loadData()
    } catch (error) {
      console.error("Failed to create user:", error)
    }
  }

  const assignRole = async (userId: string, roleId: string) => {
    try {
      await apiClient.post(`/organization/users/${userId}/assign-role`, { role_id: roleId })
      loadData()
    } catch (error) {
      console.error("Failed to assign role:", error)
    }
  }

  const removeRole = async (userId: string, roleId: string) => {
    try {
      await apiClient.delete(`/organization/users/${userId}/remove-role/${roleId}`)
      loadData()
    } catch (error) {
      console.error("Failed to remove role:", error)
    }
  }

  const deleteUser = async (userId: string) => {
    if (!confirm("Are you sure you want to delete this user?")) return
    try {
      await apiClient.delete(`/organization/users/${userId}`)
      loadData()
    } catch (error) {
      console.error("Failed to delete user:", error)
    }
  }

  const toggleUserActive = async (userId: string, activate: boolean) => {
    try {
      const endpoint = activate ? "activate" : "deactivate"
      await apiClient.patch(`/organization/users/${userId}/${endpoint}`)
      loadData()
    } catch (error) {
      console.error("Failed to update user status:", error)
    }
  }

  if (!canViewPeople) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6">{t("organization.title")}</h1>
        <p className="text-muted-foreground">You do not have permission to view this page.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("organization.title")}</h1>
      <p className="text-muted-foreground mb-6">{t("organization.description")}</p>
      
      <div className="flex gap-2 mb-6">
        <Button variant={activeTab === "company" ? "default" : "outline"} onClick={() => setActiveTab("company")}>
          {t("organization.company")}
        </Button>
        <Button variant={activeTab === "divisions" ? "default" : "outline"} onClick={() => setActiveTab("divisions")}>
          {t("organization.divisions")}
        </Button>
        <Button variant={activeTab === "people" ? "default" : "outline"} onClick={() => setActiveTab("people")}>
          {t("organization.people")}
        </Button>
        <Button variant={activeTab === "users" ? "default" : "outline"} onClick={() => setActiveTab("users")}>
          {t("organization.cyberplanUsers")}
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-8">{t("common.loading")}</div>
      ) : (
        <>
          {activeTab === "company" && (
            <div className="space-y-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>{t("organization.companyDetails")}</CardTitle>
                    <CardDescription>{t("organization.companyDetailsDesc")}</CardDescription>
                  </div>
                  {canManageOrg && (
                    <Button variant={companyEditing ? "default" : "outline"} onClick={() => {
                      if (companyEditing) {
                        saveCompany()
                      } else {
                        setCompanyEditing(true)
                      }
                    }}>
                      {companyEditing ? t("common.save") : t("common.edit")}
                    </Button>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">{t("organization.companyName")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.name || ""} onChange={e => setCompanyForm({...companyForm, name: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.name || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.registryCode")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.registry_code || ""} onChange={e => setCompanyForm({...companyForm, registry_code: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.registry_code || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.legalForm")}</label>
                      {companyEditing ? (
                        <select 
                          value={companyForm.legal_form || ""} 
                          onChange={e => setCompanyForm({...companyForm, legal_form: e.target.value})}
                          className="w-full mt-1 px-3 py-2 border rounded-md"
                        >
                          <option value="">-</option>
                          <option value="OÜ">OÜ</option>
                          <option value="AS">AS</option>
                          <option value="MTÜ">MTÜ</option>
                          <option value="FIE">FIE</option>
                          <option value="TÜ">TÜ</option>
                          <option value="SA">SA</option>
                        </select>
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.legal_form || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.registrationDate")}</label>
                      {companyEditing ? (
                        <Input type="date" value={companyForm.registration_date || ""} onChange={e => setCompanyForm({...companyForm, registration_date: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.registration_date || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.status")}</label>
                      {companyEditing ? (
                        <select 
                          value={companyForm.status || "active"} 
                          onChange={e => setCompanyForm({...companyForm, status: e.target.value})}
                          className="w-full mt-1 px-3 py-2 border rounded-md"
                        >
                          <option value="active">Active</option>
                          <option value="in_liquidation">In Liquidation</option>
                          <option value="reorganizing">Reorganizing</option>
                        </select>
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.status || "active"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.phone")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.phone || ""} onChange={e => setCompanyForm({...companyForm, phone: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.phone || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.email")}</label>
                      {companyEditing ? (
                        <Input type="email" value={companyForm.email || ""} onChange={e => setCompanyForm({...companyForm, email: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.email || "-"}</p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium">{t("organization.website")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.website || ""} onChange={e => setCompanyForm({...companyForm, website: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.website || "-"}</p>
                      )}
                    </div>
                    <div className="md:col-span-2">
                      <label className="text-sm font-medium">{t("organization.registeredAddress")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.registered_address || ""} onChange={e => setCompanyForm({...companyForm, registered_address: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.registered_address || "-"}</p>
                      )}
                    </div>
                    <div className="md:col-span-2">
                      <label className="text-sm font-medium">{t("organization.contactAddress")}</label>
                      {companyEditing ? (
                        <Input value={companyForm.contact_address || ""} onChange={e => setCompanyForm({...companyForm, contact_address: e.target.value})} className="mt-1" />
                      ) : (
                        <p className="text-muted-foreground mt-1">{company?.contact_address || "-"}</p>
                      )}
                    </div>
                  </div>
                  {companyEditing && (
                    <div className="mt-4 flex gap-2">
                      <Button onClick={() => { setCompanyEditing(false); setCompanyForm(company) }}>{t("common.cancel")}</Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === "divisions" && (
            <div className="space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>{t("organization.divisionsList")}</CardTitle>
                    <CardDescription>{t("organization.divisionsDesc")}</CardDescription>
                  </div>
                  {canManageDivisions && (
                    <Button onClick={() => { setEditingDivision(null); setDivisionForm({ code: "", name: "", description: "", parent_division_id: "", head_user_id: "" }); setDivisionModalOpen(true) }}>
                      {t("organization.addDivision")}
                    </Button>
                  )}
                </CardHeader>
                <CardContent>
                  {divisions.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">{t("organization.noDivisions")}</p>
                  ) : (
                    <div className="space-y-2">
                      {divisions.map(div => (
                        <div key={div.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium">{div.name}</p>
                            <p className="text-sm text-muted-foreground">{div.code} • {div.member_count} {t("organization.members")}</p>
                          </div>
                          <div className="flex gap-2">
                            {canManageDivisions && (
                              <>
                                <Button variant="outline" size="sm" onClick={() => {
                                  setEditingDivision(div)
                                  setDivisionForm({ code: div.code, name: div.name, description: div.description || "", parent_division_id: div.parent_division_id || "", head_user_id: div.head_user_id || "" })
                                  setDivisionModalOpen(true)
                                }}>{t("common.edit")}</Button>
                                <Button variant="destructive" size="sm" onClick={() => deleteDivision(div.id)}>{t("common.delete")}</Button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {divisionModalOpen && (
                <Card>
                  <CardHeader>
                    <CardTitle>{editingDivision ? t("organization.editDivision") : t("organization.addNewDivision")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">{t("organization.divisionCode")} *</label>
                        <Input value={divisionForm.code} onChange={e => setDivisionForm({...divisionForm, code: e.target.value})} className="mt-1" />
                      </div>
                      <div>
                        <label className="text-sm font-medium">{t("organization.divisionName")} *</label>
                        <Input value={divisionForm.name} onChange={e => setDivisionForm({...divisionForm, name: e.target.value})} className="mt-1" />
                      </div>
                      <div>
                        <label className="text-sm font-medium">{t("organization.description")}</label>
                        <Input value={divisionForm.description} onChange={e => setDivisionForm({...divisionForm, description: e.target.value})} className="mt-1" />
                      </div>
                      <div>
                        <label className="text-sm font-medium">{t("organization.parentDivision")}</label>
                        <select 
                          value={divisionForm.parent_division_id} 
                          onChange={e => setDivisionForm({...divisionForm, parent_division_id: e.target.value})}
                          className="w-full mt-1 px-3 py-2 border rounded-md"
                        >
                          <option value="">{t("organization.none")}</option>
                          {divisions.filter(d => d.id !== editingDivision?.id).map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={saveDivision}>{t("common.save")}</Button>
                        <Button variant="outline" onClick={() => setDivisionModalOpen(false)}>{t("common.cancel")}</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {activeTab === "people" && (
            <div className="space-y-4">
              {canManagePeople && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("organization.addPerson")}</CardTitle>
                    <CardDescription>{t("organization.addPersonDesc")}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2">
                      <Input 
                        placeholder={t("organization.personName")} 
                        value={newPersonName}
                        onChange={e => setNewPersonName(e.target.value)}
                      />
                      <Input 
                        placeholder={t("organization.email")} 
                        value={newPersonEmail}
                        onChange={e => setNewPersonEmail(e.target.value)}
                      />
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
                          {person.email && (
                            <div className="text-sm text-muted-foreground">{person.email}</div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {person.has_user_account ? (
                            <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
                              {t("organization.hasAccount")}
                              {person.user_roles.length > 0 && (
                                <span className="ml-1">
                                  ({person.user_roles.map(r => r.name).join(", ")})
                                </span>
                              )}
                            </span>
                          ) : (
                            <>
                              <span className="text-sm bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                {t("organization.noAccount")}
                              </span>
                              {canManageUsers && (
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={() => setCreatingFromAssetId(person.id)}
                                >
                                  {t("organization.createUser")}
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                    {people.length === 0 && (
                      <p className="text-muted-foreground text-center py-4">
                        {t("organization.noPeople")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Create User Modal for Asset */}
              {creatingFromAssetId && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                  <Card className="w-96">
                    <CardHeader>
                      <CardTitle>{t("organization.createUserAccount")}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Input 
                        placeholder={t("organization.email")} 
                        value={newUserEmailForAsset}
                        onChange={e => setNewUserEmailForAsset(e.target.value)}
                      />
                      <Input 
                        placeholder={t("organization.password")} 
                        type="password"
                        value={newUserPasswordForAsset}
                        onChange={e => setNewUserPasswordForAsset(e.target.value)}
                      />
                      <div className="flex gap-2">
                        <Button onClick={() => createUserFromPersonAsset(creatingFromAssetId)}>
                          {t("common.save")}
                        </Button>
                        <Button variant="outline" onClick={() => setCreatingFromAssetId(null)}>
                          {t("common.cancel")}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          )}

          {activeTab === "users" && (
            <div className="space-y-4">
              {canManageUsers && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("organization.addUser")}</CardTitle>
                    <CardDescription>{t("organization.addUserDesc")}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                      <Input 
                        placeholder={t("organization.userName")} 
                        value={newUserName}
                        onChange={e => setNewUserName(e.target.value)}
                      />
                      <Input 
                        placeholder={t("organization.email")} 
                        value={newUserEmail}
                        onChange={e => setNewUserEmail(e.target.value)}
                      />
                      <Input 
                        placeholder={t("organization.password")} 
                        type="password"
                        value={newUserPassword}
                        onChange={e => setNewUserPassword(e.target.value)}
                      />
                      <select 
                        className="bg-background text-foreground border-input rounded px-3 py-2"
                        value={selectedAssetForUser}
                        onChange={e => setSelectedAssetForUser(e.target.value)}
                      >
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
                            {!user.is_active && (
                              <span className="ml-2 text-xs bg-red-100 text-red-800 px-1 rounded">
                                {t("organization.inactive")}
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                          {user.linked_asset_id && (
                            <div className="text-xs text-muted-foreground">
                              {t("organization.linkedTo")}: {people.find(p => p.id === user.linked_asset_id)?.name || user.linked_asset_id}
                            </div>
                          )}
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
                            <select 
                              className="text-xs bg-background text-foreground border-input rounded px-2 py-1"
                              onChange={e => e.target.value && assignRole(user.id, e.target.value)}
                              value=""
                            >
                              <option value="">+ {t("organization.addRole")}</option>
                              {roles.filter(r => !user.roles.some(ur => ur.id === r.id)).map(role => (
                                <option key={role.id} value={role.id}>{t(`roles.${role.code}.name`)}</option>
                              ))}
                            </select>
                          )}
                          {canManageUsers && (
                            <div className="flex gap-1">
                              {user.is_active ? (
                                <Button size="sm" variant="outline" onClick={() => toggleUserActive(user.id, false)}>
                                  {t("organization.deactivate")}
                                </Button>
                              ) : (
                                <Button size="sm" variant="outline" onClick={() => toggleUserActive(user.id, true)}>
                                  {t("organization.activate")}
                                </Button>
                              )}
                              <Button size="sm" variant="destructive" onClick={() => deleteUser(user.id)}>
                                {t("common.delete")}
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {users.length === 0 && (
                      <p className="text-muted-foreground text-center py-4">
                        {t("organization.noUsers")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}