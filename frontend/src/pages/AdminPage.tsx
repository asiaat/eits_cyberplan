import { useState, useEffect } from "react"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Crown } from "lucide-react"

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  roles: string[]
  department?: string
}

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

export default function AdminPage() {
  const { hasPermission } = usePermission()
  const [activeTab, setActiveTab] = useState("users")
  
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  
  const [newUserEmail, setNewUserEmail] = useState("")
  const [newUserName, setNewUserName] = useState("")

  const canManageUsers = hasPermission("users.create")

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
    if (!newUserEmail || !newUserName) return
    try {
      await apiClient.post("/users/", {
        email: newUserEmail,
        full_name: newUserName,
        password: "tempPassword123",
      })
      setNewUserEmail("")
      setNewUserName("")
      loadData()
    } catch (error) {
      console.error("Failed to create user:", error)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Crown className="h-5 w-5" />
        <h1 className="text-2xl font-bold">Admin</h1>
      </div>

      <div className="flex gap-2 border-b">
        <button
          className={`px-4 py-2 ${activeTab === "users" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          Users
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "roles" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("roles")}
        >
          Roles
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "permissions" ? "border-b-2 border-primary" : ""}`}
          onClick={() => setActiveTab("permissions")}
        >
          Permissions
        </button>
      </div>

      {activeTab === "users" && (
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {canManageUsers && (
              <div className="flex gap-2 p-4 border rounded">
                <input
                  type="email"
                  placeholder="Email"
                  value={newUserEmail}
                  onChange={e => setNewUserEmail(e.target.value)}
                  className="border rounded px-2 py-1 flex-1"
                />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={newUserName}
                  onChange={e => setNewUserName(e.target.value)}
                  className="border rounded px-2 py-1 flex-1"
                />
                <Button onClick={createUser}>Add User</Button>
              </div>
            )}
            
            <div className="space-y-2">
              {users.map(user => (
                <div key={user.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{user.full_name}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                  <div className="flex items-center gap-2">
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

      {activeTab === "roles" && (
        <Card>
          <CardHeader>
            <CardTitle>E-ITS Roles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {roles.map(role => (
                <div key={role.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{role.role_name}</div>
                    {role.description && (
                      <div className="text-sm text-muted-foreground">{role.description}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "permissions" && (
        <Card>
          <CardHeader>
            <CardTitle>Permissions</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const categories = [...new Set(permissions.map(p => p.category || "other"))]
              return (
                <div className="space-y-4">
                  {categories.map(cat => (
                    <div key={cat}>
                      <div className="font-medium text-sm mb-2 capitalize">{cat}</div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {permissions
                          .filter(p => p.category === cat)
                          .map(perm => (
                            <div key={perm.id} className="text-sm border p-2 rounded">
                              <div>{perm.name}</div>
                              <div className="text-xs text-muted-foreground">{perm.code}</div>
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
    </div>
  )
}