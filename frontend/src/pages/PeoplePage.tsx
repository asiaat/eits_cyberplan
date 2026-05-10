import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Building2, Mail, Phone, Edit, Trash2, X } from "lucide-react"

interface Person {
  id: string
  name: string
  email: string | null
  position: string | null
  phone: string | null
  notes: string | null
  organizations: { tenant_id: string; tenant_name: string; role: string | null }[]
  has_user_account: boolean
  user_roles: { id: string; code: string; name: string }[]
}

interface Organization {
  id: string
  name: string
}

export default function PeoplePage() {
  const { t } = useTranslation()
  const { isAdmin, isISM } = usePermission()
  
  const canManage = isAdmin || isISM

  const [people, setPeople] = useState<Person[]>([])
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  const [showCreate, setShowCreate] = useState(false)
  const [newPerson, setNewPerson] = useState({
    name: "",
    email: "",
    position: "",
    phone: "",
    notes: "",
  })

  const [editingPerson, setEditingPerson] = useState<Person | null>(null)
  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    position: "",
    phone: "",
    notes: "",
  })

  const [linkingOrg, setLinkingOrg] = useState<Person | null>(null)
  const [linkOrgId, setLinkOrgId] = useState("")
  const [linkOrgRole, setLinkOrgRole] = useState("")

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [peopleRes, orgsRes] = await Promise.all([
        apiClient.get("/persons/"),
        apiClient.get("/tenants/my-organizations"),
      ])
      setPeople(peopleRes.data)
      setOrganizations(orgsRes.data)
    } catch (error) {
      console.error("Failed to load data:", error)
    }
    setLoading(false)
  }

  const createPerson = async () => {
    if (!newPerson.name) return
    try {
      await apiClient.post("/persons/", {
        name: newPerson.name,
        email: newPerson.email || null,
        position: newPerson.position || null,
        phone: newPerson.phone || null,
        notes: newPerson.notes || null,
      })
      setShowCreate(false)
      setNewPerson({ name: "", email: "", position: "", phone: "", notes: "" })
      loadData()
    } catch (error) {
      console.error("Failed to create person:", error)
    }
  }

  const updatePerson = async () => {
    if (!editingPerson) return
    try {
      await apiClient.patch(`/persons/${editingPerson.id}`, {
        name: editForm.name,
        email: editForm.email || null,
        position: editForm.position || null,
        phone: editForm.phone || null,
        notes: editForm.notes || null,
      })
      setEditingPerson(null)
      loadData()
    } catch (error) {
      console.error("Failed to update person:", error)
    }
  }

  const deletePerson = async (personId: string) => {
    if (!confirm(t("common.confirmDelete") || "Are you sure?")) return
    try {
      await apiClient.delete(`/persons/${personId}`)
      loadData()
    } catch (error) {
      console.error("Failed to delete person:", error)
    }
  }

  const linkToOrganization = async () => {
    if (!linkingOrg || !linkOrgId) return
    try {
      await apiClient.post(`/persons/${linkingOrg.id}/organizations`, {
        tenant_id: linkOrgId,
        role: linkOrgRole || null,
      })
      setLinkingOrg(null)
      setLinkOrgId("")
      setLinkOrgRole("")
      loadData()
    } catch (error) {
      console.error("Failed to link person:", error)
    }
  }

  const unlinkFromOrganization = async (personId: string, tenantId: string) => {
    try {
      await apiClient.delete(`/persons/${personId}/organizations/${tenantId}`)
      loadData()
    } catch (error) {
      console.error("Failed to unlink person:", error)
    }
  }

  const filteredPeople = people.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.email && p.email.toLowerCase().includes(search.toLowerCase())) ||
    (p.position && p.position.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">{t("people.title") || "People"}</h1>
        {canManage && (
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t("people.addPerson") || "Add Person"}
          </Button>
        )}
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("people.search") || "Search people..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">{t("common.loading")}</div>
      ) : (
        <div className="grid gap-4">
          {filteredPeople.map((person) => (
            <Card key={person.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{person.name}</h3>
                      {person.has_user_account && (
                        <Badge variant="secondary">
                          {t("people.hasAccount") || "Has Account"}
                        </Badge>
                      )}
                    </div>
                    {person.position && (
                      <p className="text-muted-foreground">{person.position}</p>
                    )}
                    <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                      {person.email && (
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {person.email}
                        </span>
                      )}
                      {person.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          {person.phone}
                        </span>
                      )}
                    </div>

                    <div className="mt-4">
                      <h4 className="text-sm font-medium mb-2">
                        {t("people.organizations") || "Organizations"}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {person.organizations.map((org) => (
                          <div
                            key={org.tenant_id}
                            className="flex items-center gap-2 bg-secondary px-3 py-1 rounded-md"
                          >
                            <Building2 className="h-3 w-3" />
                            <span className="text-sm">{org.tenant_name}</span>
                            {org.role && (
                              <Badge variant="outline" className="text-xs">
                                {org.role}
                              </Badge>
                            )}
                            <button
                              onClick={() =>
                                unlinkFromOrganization(person.id, org.tenant_id)
                              }
                              className="text-muted-foreground hover:text-destructive"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                        {canManage && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setLinkingOrg(person)}
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {t("people.linkOrg") || "Link Org"}
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>

                  {canManage && (
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingPerson(person)
                          setEditForm({
                            name: person.name,
                            email: person.email || "",
                            position: person.position || "",
                            phone: person.phone || "",
                            notes: person.notes || "",
                          })
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deletePerson(person.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredPeople.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              {t("people.noPeople") || "No people found"}
            </div>
          )}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("people.addPerson")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">{t("people.name")} *</label>
                <Input
                  value={newPerson.name}
                  onChange={(e) =>
                    setNewPerson({ ...newPerson, name: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.email")}</label>
                <Input
                  type="email"
                  value={newPerson.email}
                  onChange={(e) =>
                    setNewPerson({ ...newPerson, email: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.position")}</label>
                <Input
                  value={newPerson.position}
                  onChange={(e) =>
                    setNewPerson({ ...newPerson, position: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.phone")}</label>
                <Input
                  value={newPerson.phone}
                  onChange={(e) =>
                    setNewPerson({ ...newPerson, phone: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.notes")}</label>
                <Input
                  value={newPerson.notes}
                  onChange={(e) =>
                    setNewPerson({ ...newPerson, notes: e.target.value })
                  }
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={createPerson}>{t("common.save")}</Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCreate(false)}
                >
                  {t("common.cancel")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {editingPerson && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("people.editPerson")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">{t("people.name")} *</label>
                <Input
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.email")}</label>
                <Input
                  type="email"
                  value={editForm.email}
                  onChange={(e) =>
                    setEditForm({ ...editForm, email: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.position")}</label>
                <Input
                  value={editForm.position}
                  onChange={(e) =>
                    setEditForm({ ...editForm, position: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.phone")}</label>
                <Input
                  value={editForm.phone}
                  onChange={(e) =>
                    setEditForm({ ...editForm, phone: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.notes")}</label>
                <Input
                  value={editForm.notes}
                  onChange={(e) =>
                    setEditForm({ ...editForm, notes: e.target.value })
                  }
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={updatePerson}>{t("common.save")}</Button>
                <Button
                  variant="outline"
                  onClick={() => setEditingPerson(null)}
                >
                  {t("common.cancel")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {linkingOrg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[400px]">
            <CardHeader>
              <CardTitle>{t("people.linkToOrg")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">{t("people.selectOrg")}</label>
                <select
                  className="w-full mt-1 bg-background text-foreground border-input rounded px-3 py-2"
                  value={linkOrgId}
                  onChange={(e) => setLinkOrgId(e.target.value)}
                >
                  <option value="">
                    {t("people.selectOrg") || "Select organization"}
                  </option>
                  {organizations
                    .filter(
                      (org) =>
                        !linkingOrg.organizations.some(
                          (o) => o.tenant_id === org.id
                        )
                    )
                    .map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">{t("people.role")}</label>
                <Input
                  placeholder={t("people.rolePlaceholder") || "e.g. Manager, Contact"}
                  value={linkOrgRole}
                  onChange={(e) => setLinkOrgRole(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={linkToOrganization}>{t("common.save")}</Button>
                <Button variant="outline" onClick={() => setLinkingOrg(null)}>
                  {t("common.cancel")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}