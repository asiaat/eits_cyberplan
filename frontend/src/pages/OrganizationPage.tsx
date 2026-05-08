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
  user_roles: { id: string; code: string; name: string }[]
}

interface UserWithRoles {
  id: string
  email: string
  name: string
  is_active: boolean
  roles: { id: string; code: string; name: string }[]
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
  
  const [activeTab, setActiveTab] = useState("people")
  const [people, setPeople] = useState<PersonAsset[]>([])
  const [users, setUsers] = useState<UserWithRoles[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  
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
  const canCreatePerson = hasPermission("assets.create")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
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
      console.error("Failed to load organization data:", error)
    }
    setLoading(false)
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
          {activeTab === "people" && (
            <div className="space-y-4">
              {canCreatePerson && (
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
                        className="border rounded px-3 py-2"
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
                              {role.name}
                              {canManageUsers && (
                                <button onClick={() => removeRole(user.id, role.id)} className="text-red-500">x</button>
                              )}
                            </span>
                          ))}
                          {canManageUsers && (
                            <select 
                              className="text-xs border rounded px-2 py-1"
                              onChange={e => e.target.value && assignRole(user.id, e.target.value)}
                              value=""
                            >
                              <option value="">+ {t("organization.addRole")}</option>
                              {roles.filter(r => !user.roles.some(ur => ur.id === r.id)).map(role => (
                                <option key={role.id} value={role.id}>{role.name}</option>
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