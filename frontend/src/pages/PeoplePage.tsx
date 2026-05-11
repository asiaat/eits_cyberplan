import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Plus, Search, Building2, Mail, Phone, Edit, Trash2, User } from "lucide-react"

interface Person {
  id: string
  national_id: string | null
  first_name: string
  last_name: string
  name: string
  date_of_birth: string | null
  email: string | null
  phone: string | null
  additional_info: string | null
  organizations: { tenant_id: string; tenant_name: string; role: string | null }[]
  has_user_account: boolean
  user_roles: { id: string; code: string; name: string }[]
  linked_org_ids: string[]
}

export default function PeoplePage() {
  const { t } = useTranslation()
  const { hasPermission } = usePermission()

  const canView = hasPermission("people.view")
  const canCreate = hasPermission("people.create")
  const canEdit = hasPermission("people.edit")
  const canDelete = hasPermission("people.delete")

  const [people, setPeople] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  const [showCreate, setShowCreate] = useState(false)
  const [newPerson, setNewPerson] = useState({
    national_id: "",
    first_name: "",
    last_name: "",
    date_of_birth: "",
    email: "",
    phone: "",
    additional_info: "",
  })

  const [editingPerson, setEditingPerson] = useState<Person | null>(null)
  const [editForm, setEditForm] = useState({
    national_id: "",
    first_name: "",
    last_name: "",
    date_of_birth: "",
    email: "",
    phone: "",
    additional_info: "",
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await apiClient.get("/persons/")
      setPeople(res.data)
    } catch (error) {
      console.error("Failed to load people:", error)
    }
    setLoading(false)
  }

  const createPerson = async () => {
    if (!newPerson.first_name || !newPerson.last_name) return
    try {
      await apiClient.post("/persons/", {
        national_id: newPerson.national_id || null,
        first_name: newPerson.first_name,
        last_name: newPerson.last_name,
        date_of_birth: newPerson.date_of_birth || null,
        email: newPerson.email || null,
        phone: newPerson.phone || null,
        additional_info: newPerson.additional_info || null,
      })
      setShowCreate(false)
      setNewPerson({ national_id: "", first_name: "", last_name: "", date_of_birth: "", email: "", phone: "", additional_info: "" })
      loadData()
    } catch (error) {
      console.error("Failed to create person:", error)
    }
  }

  const updatePerson = async () => {
    if (!editingPerson) return
    try {
      await apiClient.patch(`/persons/${editingPerson.id}`, {
        national_id: editForm.national_id || null,
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        date_of_birth: editForm.date_of_birth || null,
        email: editForm.email || null,
        phone: editForm.phone || null,
        additional_info: editForm.additional_info || null,
      })
      setEditingPerson(null)
      loadData()
    } catch (error) {
      console.error("Failed to update person:", error)
    }
  }

  const deletePerson = async (personId: string) => {
    if (!confirm("Delete this person? This cannot be undone.")) return
    try {
      await apiClient.delete(`/persons/${personId}`)
      loadData()
    } catch (error) {
      console.error("Failed to delete person:", error)
    }
  }

  const filteredPeople = people.filter((p) => {
    const q = search.toLowerCase()
    return (
      p.name.toLowerCase().includes(q) ||
      (p.national_id && p.national_id.toLowerCase().includes(q)) ||
      (p.email && p.email.toLowerCase().includes(q)) ||
      (p.phone && p.phone.toLowerCase().includes(q))
    )
  })

  if (!canView && !canCreate) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-4">{t("workers.title")}</h1>
        <p className="text-muted-foreground">{t("admin.noPermission")}</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">{t("workers.title")}</h1>
        {canCreate && (
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" />
            {t("workers.addPerson")}
          </Button>
        )}
      </div>

      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("workers.search")}
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
                      <div className="flex items-center gap-2">
                        <User className="h-5 w-5 text-muted-foreground" />
                        <h3 className="text-lg font-semibold">{person.name}</h3>
                      </div>
                      {person.has_user_account && (
                        <Badge variant="secondary">{t("workers.hasAccount")}</Badge>
                      )}
                      {person.linked_org_ids.length > 0 && (
                        <Badge variant="outline">{person.linked_org_ids.length} org(s)</Badge>
                      )}
                    </div>

                    {person.national_id && (
                      <p className="text-sm text-muted-foreground mt-1">
                        <span className="font-medium">ID:</span> {person.national_id}
                      </p>
                    )}
                    {person.date_of_birth && (
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">DOB:</span> {person.date_of_birth}
                      </p>
                    )}

                    <div className="flex flex-wrap gap-4 mt-2 text-sm text-muted-foreground">
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

                    {person.additional_info && (
                      <p className="text-sm text-muted-foreground mt-2 italic">{person.additional_info}</p>
                    )}

                    {person.organizations.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium mb-2">{t("workers.organizations")}</h4>
                        <div className="flex flex-wrap gap-2">
                          {person.organizations.map((org) => (
                            <div
                              key={org.tenant_id}
                              className="flex items-center gap-2 bg-secondary px-3 py-1 rounded-md"
                            >
                              <Building2 className="h-3 w-3" />
                              <span className="text-sm">{org.tenant_name}</span>
                              {org.role && (
                                <Badge variant="outline" className="text-xs">{org.role}</Badge>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {canEdit && (
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingPerson(person)
                          setEditForm({
                            national_id: person.national_id || "",
                            first_name: person.first_name,
                            last_name: person.last_name,
                            date_of_birth: person.date_of_birth || "",
                            email: person.email || "",
                            phone: person.phone || "",
                            additional_info: person.additional_info || "",
                          })
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      {canDelete && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deletePerson(person.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredPeople.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              {t("workers.noPeople")}
            </div>
          )}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("workers.addPersonCard")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("workers.name")} *</label>
                  <Input value={newPerson.first_name} onChange={e => setNewPerson({ ...newPerson, first_name: e.target.value })} placeholder={t("workers.name")} />
                </div>
                <div>
                  <label className="text-sm font-medium">{t("workers.name")} *</label>
                  <Input value={newPerson.last_name} onChange={e => setNewPerson({ ...newPerson, last_name: e.target.value })} placeholder={t("workers.name")} />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.nationalId")}</label>
                <Input value={newPerson.national_id} onChange={e => setNewPerson({ ...newPerson, national_id: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.dateOfBirth")}</label>
                <Input type="date" value={newPerson.date_of_birth} onChange={e => setNewPerson({ ...newPerson, date_of_birth: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.email")}</label>
                <Input type="email" value={newPerson.email} onChange={e => setNewPerson({ ...newPerson, email: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.phone")}</label>
                <Input value={newPerson.phone} onChange={e => setNewPerson({ ...newPerson, phone: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.notes")}</label>
                <Input value={newPerson.additional_info} onChange={e => setNewPerson({ ...newPerson, additional_info: e.target.value })} />
              </div>
              <div className="flex gap-2">
                <Button onClick={createPerson}>{t("common.save")}</Button>
                <Button variant="outline" onClick={() => setShowCreate(false)}>{t("common.cancel")}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {editingPerson && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("workers.editPersonCard")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("workers.name")} *</label>
                  <Input value={editForm.first_name} onChange={e => setEditForm({ ...editForm, first_name: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium">{t("workers.name")} *</label>
                  <Input value={editForm.last_name} onChange={e => setEditForm({ ...editForm, last_name: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.nationalId")}</label>
                <Input value={editForm.national_id} onChange={e => setEditForm({ ...editForm, national_id: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.dateOfBirth")}</label>
                <Input type="date" value={editForm.date_of_birth} onChange={e => setEditForm({ ...editForm, date_of_birth: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.email")}</label>
                <Input type="email" value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.phone")}</label>
                <Input value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium">{t("workers.notes")}</label>
                <Input value={editForm.additional_info} onChange={e => setEditForm({ ...editForm, additional_info: e.target.value })} />
              </div>
              <div className="flex gap-2">
                <Button onClick={updatePerson}>{t("common.save")}</Button>
                <Button variant="outline" onClick={() => setEditingPerson(null)}>{t("common.cancel")}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
