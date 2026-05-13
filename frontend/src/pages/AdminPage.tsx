import { useState, useEffect } from "react"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Crown, Plus, Trash2 } from "lucide-react"

interface Role {
  id: string
  role_name: string
  description: string | null
}

interface Permission {
  id: string
  code: string
  name: string
  category: string | null
}

interface User {
  id: string
  email: string
  full_name: string
  roles: string[]
}

export default function AdminPage() {
  const { isAdmin } = usePermission()
  const [activeTab, setActiveTab] = useState("roles")
  
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [rolePermissions, setRolePermissions] = useState<Record<string, string[]>>({})
  
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [showCreateRole, setShowCreateRole] = useState(false)
  const [newRoleName, setNewRoleName] = useState("")
  const [newRoleDesc, setNewRoleDesc] = useState("")
  
  const canManage = isAdmin()

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
      
      // Load permissions for each role
      loadAllRolePermissions(rolesRes.data)
    } catch (error) {
      console.error("Failed to load admin data:", error)
    }
  }

  const loadAllRolePermissions = async (rolesList: Role[]) => {
    const perms: Record<string, string[]> = {}
    for (const role of rolesList) {
      try {
        const res = await apiClient.get(`/roles/${role.id}/permissions`)
        perms[role.id] = res.data.map((p: Permission) => p.id)
      } catch {
        perms[role.id] = []
      }
    }
    setRolePermissions(perms)
  }

  const createRole = async () => {
    if (!newRoleName) return
    try {
      await apiClient.post("/roles/", {
        role_name: newRoleName,
        description: newRoleDesc || null,
      })
      setNewRoleName("")
      setNewRoleDesc("")
      setShowCreateRole(false)
      loadData()
    } catch (error) {
      console.error("Failed to create role:", error)
    }
  }

  const updateRole = async () => {
    if (!editingRole) return
    try {
      await apiClient.patch(`/roles/${editingRole.id}`, {
        role_name: editingRole.role_name,
        description: editingRole.description,
      })
      setEditingRole(null)
      loadData()
    } catch (error) {
      console.error("Failed to update role:", error)
    }
  }

  const deleteRole = async (roleId: string) => {
    if (!confirm("Delete this role?")) return
    try {
      await apiClient.delete(`/roles/${roleId}`)
      loadData()
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to delete role")
    }
  }

  const togglePermission = async (roleId: string, permId: string, hasPerm: boolean) => {
    try {
      if (hasPerm) {
        await apiClient.delete(`/roles/${roleId}/permissions/${permId}`)
      } else {
        await apiClient.post(`/roles/${roleId}/permissions`, {
          permission_id: permId,
        })
      }
      // Update local state
      setRolePermissions(prev => ({
        ...prev,
        [roleId]: hasPerm 
          ? prev[roleId].filter(id => id !== permId)
          : [...prev[roleId], permId]
      }))
    } catch (error) {
      console.error("Failed to toggle permission:", error)
    }
  }

  const getCategories = () => {
    const cats = [...new Set(permissions.map(p => p.category || "other"))]
    return cats.sort()
  }

  const getPermissionsForCategory = (category: string | null) => {
    return permissions.filter(p => (p.category || "other") === category)
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Crown className="h-5 w-5" />
        <h1 className="text-2xl font-bold">Admin</h1>
      </div>

      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 ${activeTab === "roles" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("roles")}
        >
          E-ITS Roles
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "permissions" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("permissions")}
        >
          Permissions
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "users" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          Users
        </button>
      </div>

      {activeTab === "roles" && (
        <div className="space-y-4">
          {canManage && (
            <div className="flex justify-end">
              <Button onClick={() => setShowCreateRole(true)} size="sm">
                <Plus className="h-4 w-4 mr-1" /> New Role
              </Button>
            </div>
          )}

          {showCreateRole && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Create New Role</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <input
                  type="text"
                  placeholder="Role Name (e.g., Auditor)"
                  value={newRoleName}
                  onChange={e => setNewRoleName(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                />
                <textarea
                  placeholder="Description"
                  value={newRoleDesc}
                  onChange={e => setNewRoleDesc(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
                <div className="flex gap-2">
                  <Button onClick={createRole} size="sm">Create</Button>
                  <Button variant="outline" onClick={() => setShowCreateRole(false)} size="sm">Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {roles.map(role => (
            <Card key={role.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  {editingRole?.id === role.id ? (
                    <div className="flex-1 space-y-2">
                      <input
                        type="text"
                        value={editingRole.role_name}
                        onChange={e => setEditingRole({...editingRole, role_name: e.target.value})}
                        className="w-full border rounded px-2 py-1"
                      />
                      <textarea
                        value={editingRole.description || ""}
                        onChange={e => setEditingRole({...editingRole, description: e.target.value})}
                        className="w-full border rounded px-2 py-1"
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <Button onClick={updateRole} size="sm">Save</Button>
                        <Button variant="outline" onClick={() => setEditingRole(null)} size="sm">Cancel</Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div>
                        <CardTitle className="text-lg">{role.role_name}</CardTitle>
                        {role.description && (
                          <p className="text-sm text-muted-foreground">{role.description}</p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {canManage && (
                          <>
                            <Button variant="outline" size="sm" onClick={() => setEditingRole(role)}>
                              Edit
                            </Button>
                            <Button variant="destructive" size="sm" onClick={() => deleteRole(role.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-medium mb-2">Permissions:</div>
                {getCategories().map(cat => (
                  <div key={cat} className="mb-3">
                    <div className="text-xs uppercase text-muted-foreground mb-1">{cat}</div>
                    <div className="flex flex-wrap gap-2">
                      {getPermissionsForCategory(cat).map(perm => {
                        const hasPerm = rolePermissions[role.id]?.includes(perm.id)
                        return (
                          <label 
                            key={perm.id} 
                            className={`flex items-center gap-1 text-xs px-2 py-1 rounded cursor-pointer ${
                              hasPerm ? 'bg-primary text-primary-foreground' : 'bg-secondary'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={hasPerm}
                              onChange={() => canManage && togglePermission(role.id, perm.id, hasPerm)}
                              disabled={!canManage}
                              className="sr-only"
                            />
                            {perm.name}
                            {!canManage && <span className="opacity-50 ml-1">{hasPerm ? "✓" : "○"}</span>}
                            {canManage && <span className="ml-1 opacity-70">{hasPerm ? "✓" : "○"}</span>}
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {activeTab === "permissions" && (
        <Card>
          <CardHeader>
            <CardTitle>All Permissions</CardTitle>
          </CardHeader>
          <CardContent>
            {getCategories().map(cat => (
              <div key={cat} className="mb-4">
                <div className="font-medium text-sm mb-2 capitalize">{cat}</div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {getPermissionsForCategory(cat).map(perm => (
                    <div key={perm.id} className="border rounded p-2">
                      <div className="font-medium text-sm">{perm.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{perm.code}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === "users" && (
        <Card>
          <CardHeader>
            <CardTitle>Users in Organization</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {users.map(user => (
                <div key={user.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{user.full_name}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {user.roles?.map((roleName, idx) => (
                      <span key={idx} className="text-xs bg-secondary px-2 py-1 rounded">
                        {roleName}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}