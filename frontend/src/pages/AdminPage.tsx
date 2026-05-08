import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface User {
  id: string
  email: string
  name: string
  is_active: boolean
  roles: { id: string; code: string; name: string }[]
}

interface Role {
  id: string
  code: string
  name: string
  description: string | null
  is_default: string
}

interface Permission {
  id: string
  code: string
  name: string
  description: string | null
  category: string
}

export default function AdminPage() {
  const { t } = useTranslation()
  const { hasPermission } = usePermission()
  const [activeTab, setActiveTab] = useState("users")
  
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  
  const [newUserEmail, setNewUserEmail] = useState("")
  const [newUserName, setNewUserName] = useState("")
  const [newUserPassword, setNewUserPassword] = useState("")
  const [newRoleCode, setNewRoleCode] = useState("")
  const [newRoleName, setNewRoleName] = useState("")
  const [newRoleDesc, setNewRoleDesc] = useState("")

  const canManageUsers = hasPermission("users.create")
  const canManageRoles = hasPermission("roles.manage")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [usersRes, rolesRes, permsRes] = await Promise.all([
        apiClient.get("/users/"),
        apiClient.get("/roles/"),
        apiClient.get("/roles/permissions"),
      ])
      setUsers(usersRes.data)
      setRoles(rolesRes.data)
      setPermissions(permsRes.data)
    } catch (error) {
      console.error("Failed to load admin data:", error)
    }
  }

  const createUser = async () => {
    if (!newUserEmail || !newUserName || !newUserPassword) return
    try {
      await apiClient.post("/users/", {
        email: newUserEmail,
        name: newUserName,
        password: newUserPassword,
      })
      setNewUserEmail("")
      setNewUserName("")
      setNewUserPassword("")
      loadData()
    } catch (error) {
      console.error("Failed to create user:", error)
    }
  }

  const createRole = async () => {
    if (!newRoleCode || !newRoleName) return
    try {
      await apiClient.post("/roles/", {
        code: newRoleCode,
        name: newRoleName,
        description: newRoleDesc || null,
      })
      setNewRoleCode("")
      setNewRoleName("")
      setNewRoleDesc("")
      loadData()
    } catch (error) {
      console.error("Failed to create role:", error)
    }
  }

  const assignRole = async (userId: string, roleId: string) => {
    try {
      await apiClient.post(`/users/${userId}/roles/`, { role_id: roleId })
      loadData()
    } catch (error) {
      console.error("Failed to assign role:", error)
    }
  }

  const removeRole = async (userId: string, roleId: string) => {
    try {
      await apiClient.delete(`/users/${userId}/roles/${roleId}`)
      loadData()
    } catch (error) {
      console.error("Failed to remove role:", error)
    }
  }

  const deleteRole = async (roleId: string) => {
    try {
      await apiClient.delete(`/roles/${roleId}`)
      loadData()
    } catch (error) {
      console.error("Failed to delete role:", error)
    }
  }

  const getRolePermissions = async (roleId: string) => {
    try {
      const res = await apiClient.get(`/roles/${roleId}/permissions`)
      return res.data
    } catch (error) {
      console.error("Failed to get role permissions:", error)
      return []
    }
  }

  const updateRolePermissions = async (roleId: string, permissionIds: string[]) => {
    try {
      await apiClient.post(`/roles/${roleId}/permissions`, { permission_ids: permissionIds })
      loadData()
    } catch (error) {
      console.error("Failed to update role permissions:", error)
    }
  }

  if (!canManageUsers && !canManageRoles) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-6">{t("admin.title")}</h1>
        <p className="text-muted-foreground">You do not have permission to access this page.</p>
      </div>
    )
  }

  const categories = [...new Set(permissions.map(p => p.category))]

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t("admin.title")}</h1>
      
      <div className="flex gap-2 mb-4">
        <Button variant={activeTab === "users" ? "default" : "outline"} onClick={() => setActiveTab("users")}>{t("admin.usersTab")}</Button>
        <Button variant={activeTab === "roles" ? "default" : "outline"} onClick={() => setActiveTab("roles")}>{t("admin.rolesTab")}</Button>
        <Button variant={activeTab === "permissions" ? "default" : "outline"} onClick={() => setActiveTab("permissions")}>{t("admin.permissionsTab")}</Button>
      </div>

      {activeTab === "users" && (
        <Card>
          <CardHeader>
            <CardTitle>{t("admin.userManagement")}</CardTitle>
          </CardHeader>
          <CardContent>
            {canManageUsers && (
              <div className="flex gap-2 mb-4">
                <Input placeholder={t("admin.email")} value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} />
                <Input placeholder={t("admin.name")} value={newUserName} onChange={e => setNewUserName(e.target.value)} />
                <Input placeholder={t("admin.password")} type="password" value={newUserPassword} onChange={e => setNewUserPassword(e.target.value)} />
                <Button onClick={createUser}>{t("admin.addUser")}</Button>
              </div>
            )}
            
            <div className="space-y-2">
              {users.map(user => (
                <div key={user.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{user.name}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {user.roles?.map(role => (
                      <span key={role.id} className="text-xs bg-secondary px-2 py-1 rounded">
                        {t(role.name)}
                        {canManageRoles && (
                          <button onClick={() => removeRole(user.id, role.id)} className="ml-1 text-red-500">x</button>
                        )}
                      </span>
                    ))}
                    {canManageRoles && (
                      <select 
                        className="text-sm border rounded px-2 py-1"
                        onChange={e => e.target.value && assignRole(user.id, e.target.value)}
                        value=""
                      >
                        <option value="">{t("admin.addRole")}</option>
                        {roles.filter(r => !user.roles?.some(ur => ur.id === r.id)).map(role => (
                          <option key={role.id} value={role.id}>{t(role.name)}</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "roles" && (
        <Card>
          <CardHeader>
            <CardTitle>{t("admin.roleManagement")}</CardTitle>
          </CardHeader>
          <CardContent>
            {canManageRoles && (
              <div className="flex gap-2 mb-4">
                <Input placeholder={t("admin.roleCode")} value={newRoleCode} onChange={e => setNewRoleCode(e.target.value)} />
                <Input placeholder={t("admin.roleName")} value={newRoleName} onChange={e => setNewRoleName(e.target.value)} />
                <Input placeholder={t("admin.description")} value={newRoleDesc} onChange={e => setNewRoleDesc(e.target.value)} />
                <Button onClick={createRole}>{t("admin.createRole")}</Button>
              </div>
            )}
            
            <div className="space-y-2">
              {roles.map(role => (
                <div key={role.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{t(role.name)}</div>
                    <div className="text-sm text-muted-foreground">
                      {role.code} {role.is_default === "true" && <span className="bg-secondary px-1 rounded text-xs">{t("admin.eitsDefault")}</span>}
                    </div>
                    {role.description && <div className="text-sm text-muted-foreground">{t(role.description)}</div>}
                  </div>
                  {canManageRoles && role.is_default === "false" && (
                    <Button variant="destructive" size="sm" onClick={() => deleteRole(role.id)}>Delete</Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "permissions" && (
        <Card>
          <CardHeader>
            <CardTitle>{t("admin.permissionConfig")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {t("admin.permissionConfigDesc")}
            </p>
            
            {roles.map(role => (
              <RolePermissionEditor 
                key={role.id}
                role={role}
                permissions={permissions}
                categories={categories}
                canEdit={canManageRoles}
                getRolePermissions={getRolePermissions}
                updateRolePermissions={updateRolePermissions}
              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function RolePermissionEditor({
  role,
  permissions,
  categories,
  canEdit,
  getRolePermissions,
  updateRolePermissions,
}: {
  role: Role
  permissions: Permission[]
  categories: string[]
  canEdit: boolean
  getRolePermissions: (roleId: string) => Promise<Permission[]>
  updateRolePermissions: (roleId: string, permIds: string[]) => void
}) {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [rolePermissions, setRolePermissions] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const togglePermission = (permId: string) => {
    if (!canEdit) return
    const newPerms = rolePermissions.includes(permId)
      ? rolePermissions.filter(id => id !== permId)
      : [...rolePermissions, permId]
    setRolePermissions(newPerms)
    updateRolePermissions(role.id, newPerms)
  }

  const openEditor = async () => {
    if (!isOpen) {
      setLoading(true)
      const perms = await getRolePermissions(role.id)
      setRolePermissions(perms.map(p => p.id))
      setLoading(false)
    }
    setIsOpen(!isOpen)
  }

  return (
    <div className="border rounded mb-2">
      <div className="flex items-center justify-between p-2 cursor-pointer hover:bg-accent" onClick={openEditor}>
        <div className="font-medium">{t(role.name)}</div>
        <div className="text-sm text-muted-foreground">{role.code}</div>
      </div>
      
      {isOpen && (
        <div className="p-4 border-t">
          {loading ? (
            <div>Loading permissions...</div>
          ) : (
            <div className="space-y-4">
              {categories.map(cat => (
                <div key={cat}>
                  <div className="font-medium text-sm mb-2 capitalize">{cat}</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {permissions
                      .filter(p => p.category === cat)
                      .map(perm => (
                        <label key={perm.id} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={rolePermissions.includes(perm.id)}
                            onChange={() => togglePermission(perm.id)}
                            disabled={!canEdit}
                          />
                          <span>{perm.name}</span>
                        </label>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}