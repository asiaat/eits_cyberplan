import { useState, useEffect } from "react"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Crown, Plus } from "lucide-react"
import RoleAccordion from "@/components/RoleAccordion"

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

interface PendingChanges {
  [roleId: string]: {
    toAdd: string[]
    toRemove: string[]
  }
}

export default function AdminPage() {
  const { isAdmin } = usePermission()
  const [activeTab, setActiveTab] = useState("roles")
  
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [rolePermissions, setRolePermissions] = useState<Record<string, string[]>>({})
  
  // UI State
  const [expandedRoleId, setExpandedRoleId] = useState<string | null>(null)
  const [editingRoleId, setEditingRoleId] = useState<string | null>(null)
  const [showCreateRole, setShowCreateRole] = useState(false)
  
  // Form State
  const [newRoleName, setNewRoleName] = useState("")
  const [newRoleDesc, setNewRoleDesc] = useState("")
  
  // Pending Changes State
  const [pendingChanges, setPendingChanges] = useState<PendingChanges>({})
  
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
      
      await loadAllRolePermissions(rolesRes.data)
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

  const toggleExpand = (roleId: string) => {
    if (expandedRoleId === roleId) {
      setExpandedRoleId(null)
    } else {
      setExpandedRoleId(roleId)
      // Clear pending changes when collapsing
      if (expandedRoleId !== roleId) {
        setPendingChanges(prev => {
          const newChanges = { ...prev }
          delete newChanges[roleId]
          return newChanges
        })
      }
    }
  }

  const startEdit = (roleId: string) => {
    setExpandedRoleId(roleId) // Ensure expanded
    setEditingRoleId(roleId)
  }

  const cancelEdit = () => {
    // Clear pending changes
    setPendingChanges({})
    setEditingRoleId(null)
  }

  const saveRoleEdit = async (roleId: string, name: string, desc: string) => {
    try {
      await apiClient.patch(`/roles/${roleId}`, {
        role_name: name,
        description: desc || null,
      })
      setEditingRoleId(null)
      // Save permission changes too
      await savePermissionChanges(roleId)
      loadData()
    } catch (error) {
      console.error("Failed to update role:", error)
    }
  }

  const deleteRole = async (roleId: string) => {
    try {
      await apiClient.delete(`/roles/${roleId}`)
      setExpandedRoleId(null)
      setEditingRoleId(null)
      loadData()
    } catch (error: any) {
      alert(error.response?.data?.detail || "Failed to delete role")
    }
  }

  const togglePermission = (roleId: string, permId: string, wasAdded: boolean) => {
    setPendingChanges(prev => {
      const existing = prev[roleId] || { toAdd: [], toRemove: [] }
      
      let toAdd = [...existing.toAdd]
      let toRemove = [...existing.toRemove]
      
      if (wasAdded) {
        // Removing - add to toRemove if not already there
        toRemove.push(permId)
        toAdd = toAdd.filter(id => id !== permId)
      } else {
        // Adding - add to toAdd if not already there
        toAdd.push(permId)
        toRemove = toRemove.filter(id => id !== permId)
      }
      
      return {
        ...prev,
        [roleId]: { toAdd, toRemove }
      }
    })
  }

  const savePermissionChanges = async (roleId: string) => {
    const changes = pendingChanges[roleId]
    if (!changes || (changes.toAdd.length === 0 && changes.toRemove.length === 0)) {
      return
    }

    try {
      // Add permissions
      for (const permId of changes.toAdd) {
        await apiClient.post(`/roles/${roleId}/permissions`, {
          permission_id: permId,
        })
      }
      
      // Remove permissions
      for (const permId of changes.toRemove) {
        await apiClient.delete(`/roles/${roleId}/permissions/${permId}`)
      }
      
      // Clear pending changes for this role
      setPendingChanges(prev => {
        const newChanges = { ...prev }
        delete newChanges[roleId]
        return newChanges
      })
      
      loadData()
    } catch (error) {
      console.error("Failed to save permissions:", error)
    }
  }

  const saveAll = async (roleId: string, name: string, desc: string) => {
    await saveRoleEdit(roleId, name, desc)
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

  const hasPermissionChanges = (roleId: string) => {
    const changes = pendingChanges[roleId]
    return changes && (changes.toAdd.length > 0 || changes.toRemove.length > 0)
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
        <div className="space-y-3">
          {/* Roles Accordions */}
          {roles.map(role => (
            <RoleAccordion
              key={role.id}
              role={role}
              allPermissions={permissions}
              assignedPermissions={rolePermissions[role.id] || []}
              canEdit={canManage}
              isExpanded={expandedRoleId === role.id}
              onToggleExpand={() => toggleExpand(role.id)}
              isEditing={editingRoleId === role.id}
              onStartEdit={() => startEdit(role.id)}
              onCancelEdit={cancelEdit}
              onSave={(name, desc) => saveAll(role.id, name, desc)}
              onTogglePermission={(permId, added) => togglePermission(role.id, permId, added)}
              onDelete={() => deleteRole(role.id)}
              hasPermissionChanges={hasPermissionChanges(role.id)}
            />
          ))}

          {/* Create New Role Section */}
          <div className="mt-4">
            {showCreateRole ? (
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
                    placeholder="Description (optional)"
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
            ) : (
              canManage && (
                <button
                  onClick={() => setShowCreateRole(true)}
                  className="w-full p-4 border-2 border-dashed rounded-lg text-muted-foreground hover:text-foreground hover:border-primary transition-colors flex items-center justify-center gap-2"
                >
                  <Plus className="h-5 w-5" />
                  Create New Role
                </button>
              )
            )}
          </div>
        </div>
      )}

      {activeTab === "permissions" && (
        <Card>
          <CardHeader>
            <CardTitle>All Permissions</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const categories = [...new Set(permissions.map(p => p.category || "other"))].sort()
              return (
                <div className="space-y-4">
                  {categories.map(cat => (
                    <div key={cat}>
                      <div className="font-medium text-sm mb-2 capitalize">{cat}</div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {permissions
                          .filter(p => (p.category || "other") === cat)
                          .map(perm => (
                            <div key={perm.id} className="border rounded p-2">
                              <div className="font-medium text-sm">{perm.name}</div>
                              <div className="text-xs text-muted-foreground font-mono">{perm.code}</div>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })()}
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