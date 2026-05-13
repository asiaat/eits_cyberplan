import { useState, useEffect, useCallback } from "react"
import { useTranslation } from "@/lib/i18n"
import { usePermission } from "@/hooks/use-permission"
import { apiClient } from "@/lib/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Plus, Search, Building2, Mail, Phone, Edit, Trash2, User,
  X, ChevronRight, Users as UsersIcon,
} from "lucide-react"

interface OrgInfo {
  id: string
  name: string
}

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

interface PersonAsset {
  id: string
  name: string
  email: string | null
  description: string | null
  owner_user_id: string | null
  has_user_account: boolean
  user_roles: { id: string; code: string; name: string; is_default?: string }[]
  person_id: string | null
  linked: boolean
}

export default function SupportPeoplePage() {
  const { t } = useTranslation()
  const { hasPermission, isAdmin, isISM } = usePermission()

  const canAdmin = isAdmin() || isISM()
  const canCreate = hasPermission("people.create")
  const canLink = hasPermission("people.view")

  const [organizations, setOrganizations] = useState<OrgInfo[]>([])
  const [currentOrgId, setCurrentOrgId] = useState<string | null>(null)

  const [persons, setPersons] = useState<Person[]>([])
  const [workers, setWorkers] = useState<PersonAsset[]>([])
  const [availablePersons, setAvailablePersons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const [activeTab, setActiveTab] = useState<"people" | "workers">("people")
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
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

  const [showLinkToOrg, setShowLinkToOrg] = useState(false)
  const [linkOrgId, setLinkOrgId] = useState("")
  const [linkRole, setLinkRole] = useState("")

  const [linkWorkerPersonId, setLinkWorkerPersonId] = useState("")
  const [linkWorkerRole, setLinkWorkerRole] = useState("")

  useEffect(() => {
    loadOrganizations()
  }, [])

  useEffect(() => {
    if (currentOrgId) {
      loadData()
    }
  }, [currentOrgId])

  const loadOrganizations = async () => {
    try {
      const res = await apiClient.get("/tenants/my-organizations")
      const orgs = res.data
      setOrganizations(orgs)
      if (orgs.length > 0 && !currentOrgId) {
        const stored = localStorage.getItem("current_org_id")
        const match = stored && orgs.find((o: OrgInfo) => o.id === stored)
        const defaultOrg = match ? match.id : orgs[0].id
        setCurrentOrgId(defaultOrg)
        localStorage.setItem("current_org_id", defaultOrg)
      }
    } catch (error) {
      console.error("Failed to load organizations:", error)
    }
  }

  const loadData = useCallback(async () => {
    if (!currentOrgId) return
    setLoading(true)
    try {
      const [personsRes, workersRes, availRes] = await Promise.all([
        apiClient.get("/persons/"),
        apiClient.get("/organization/people"),
        apiClient.get("/organization/people/available"),
      ])
      setPersons(personsRes.data)
      setWorkers(workersRes.data)
      setAvailablePersons(availRes.data)
    } catch (error) {
      console.error("Failed to load data:", error)
    }
    setLoading(false)
  }, [currentOrgId])

  const switchOrg = (orgId: string) => {
    setCurrentOrgId(orgId)
    setSelectedPerson(null)
    localStorage.setItem("current_org_id", orgId)
  }

  const filteredPersons = persons.filter((p) => {
    const q = search.toLowerCase()
    return (
      p.name.toLowerCase().includes(q) ||
      (p.national_id && p.national_id.toLowerCase().includes(q)) ||
      (p.email && p.email.toLowerCase().includes(q)) ||
      (p.phone && p.phone.toLowerCase().includes(q))
    )
  })

  if (!canLink) {
    return (
      <div>
        <h1 className="text-3xl font-bold mb-4">{t("support.people.title")}</h1>
        <p className="text-muted-foreground">{t("admin.noPermission")}</p>
      </div>
    )
  }

  const currentOrgName = organizations.find(o => o.id === currentOrgId)?.name || ""

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">{t("support.people.title")}</h1>
        <div className="flex items-center gap-4">
          {canAdmin ? (
            <select
              className="bg-background text-foreground border-input rounded px-3 py-2 min-w-[200px]"
              value={currentOrgId || ""}
              onChange={(e) => switchOrg(e.target.value)}
            >
              {organizations.map(org => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
          ) : (
            <span className="text-sm font-medium bg-secondary px-3 py-2 rounded">{currentOrgName}</span>
          )}
        </div>
      </div>

      {canAdmin && (
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t("support.people.search")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" />
              {t("support.people.addPerson")}
            </Button>
          )}
        </div>
      )}

      {!canAdmin && (
        <div className="relative mb-6 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("support.people.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      )}

      <div className="flex gap-2 mb-6">
        <Button
          variant={activeTab === "people" ? "default" : "outline"}
          onClick={() => setActiveTab("people")}
        >
          <UsersIcon className="h-4 w-4 mr-2" />
          {t("support.people.tabPeople")}
        </Button>
        <Button
          variant={activeTab === "workers" ? "default" : "outline"}
          onClick={() => setActiveTab("workers")}
        >
          <Building2 className="h-4 w-4 mr-2" />
          {t("support.people.tabWorkers")}
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-8">{t("common.loading")}</div>
      ) : (
        <>
          {activeTab === "people" && (
            <div className="flex gap-6">
              <div className="flex-1 min-w-0">
                {filteredPersons.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {t("support.people.noPeople")}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredPersons.map((person) => (
                      <Card
                        key={person.id}
                        className={cn(
                          "cursor-pointer transition-colors hover:bg-accent/50",
                          selectedPerson?.id === person.id && "ring-2 ring-primary"
                        )}
                        onClick={() => setSelectedPerson(person)}
                      >
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              <User className="h-5 w-5 text-muted-foreground" />
                              <div>
                                <div className="font-semibold">{person.name}</div>
                                {person.national_id && (
                                  <div className="text-xs text-muted-foreground">{person.national_id}</div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {person.has_user_account && (
                                <Badge variant="secondary" className="text-xs">{t("support.people.hasAccount")}</Badge>
                              )}
                              {person.linked_org_ids.length > 0 && (
                                <Badge variant="outline" className="text-xs">
                                  {person.linked_org_ids.length} {person.linked_org_ids.length === 1 ? "org" : "orgs"}
                                </Badge>
                              )}
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            </div>
                          </div>
                          {person.email && (
                            <div className="flex items-center gap-1 mt-1 text-sm text-muted-foreground ml-7">
                              <Mail className="h-3 w-3" />
                              {person.email}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {selectedPerson && (
                <div className="w-[480px] shrink-0 border rounded-lg bg-card p-6 h-fit">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">{t("support.people.detailTitle")}</h3>
                    <button
                      onClick={() => setSelectedPerson(null)}
                      className="p-1 rounded hover:bg-accent"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <User className="h-5 w-5 text-muted-foreground" />
                      <span className="text-xl font-semibold">{selectedPerson.name}</span>
                      {selectedPerson.has_user_account && (
                        <Badge variant="secondary">{t("support.people.hasAccount")}</Badge>
                      )}
                    </div>

                    {selectedPerson.national_id && (
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">{t("support.people.nationalId")}:</span>
                        </div>
                        <div className="font-medium">{selectedPerson.national_id}</div>
                      </div>
                    )}

                    {selectedPerson.date_of_birth && (
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">{t("support.people.dateOfBirth")}:</span>
                        </div>
                        <div className="font-medium">{selectedPerson.date_of_birth}</div>
                      </div>
                    )}

                    {selectedPerson.email && (
                      <div className="flex items-center gap-2 text-sm">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{selectedPerson.email}</span>
                      </div>
                    )}

                    {selectedPerson.phone && (
                      <div className="flex items-center gap-2 text-sm">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{selectedPerson.phone}</span>
                      </div>
                    )}

                    {selectedPerson.additional_info && (
                      <div className="text-sm">
                        <span className="text-muted-foreground">{t("support.people.additionalInfo")}:</span>
                        <p className="mt-1 italic">{selectedPerson.additional_info}</p>
                      </div>
                    )}

                    {selectedPerson.organizations.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium mb-2">{t("support.people.linkedOrganizations")}</h4>
                        <div className="space-y-2">
                          {selectedPerson.organizations.map((org) => (
                            <div
                              key={org.tenant_id}
                              className="flex items-center justify-between bg-secondary px-3 py-2 rounded"
                            >
                              <div className="flex items-center gap-2">
                                <Building2 className="h-3 w-3" />
                                <span className="text-sm font-medium">{org.tenant_name}</span>
                                {org.role && (
                                  <Badge variant="outline" className="text-xs">{org.role}</Badge>
                                )}
                              </div>
                              {canAdmin && (
                                <button
                                  onClick={() => unlinkOrg(selectedPerson.id, org.tenant_id)}
                                  className="text-xs text-destructive hover:underline"
                                >
                                  {t("support.people.unlink")}
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2 pt-4 border-t">
                      {canAdmin && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setEditingPerson(selectedPerson)
                              setEditForm({
                                national_id: selectedPerson.national_id || "",
                                first_name: selectedPerson.first_name,
                                last_name: selectedPerson.last_name,
                                date_of_birth: selectedPerson.date_of_birth || "",
                                email: selectedPerson.email || "",
                                phone: selectedPerson.phone || "",
                                additional_info: selectedPerson.additional_info || "",
                              })
                            }}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            {t("common.edit")}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setLinkOrgId(currentOrgId || "")
                              setLinkRole("")
                              setShowLinkToOrg(true)
                            }}
                          >
                            <Building2 className="h-4 w-4 mr-1" />
                            {t("support.people.linkToOrg")}
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => deletePerson(selectedPerson.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            {t("common.delete")}
                          </Button>
                        </>
                      )}
                      {!canAdmin && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setLinkOrgId(currentOrgId || "")
                            setLinkRole("")
                            setShowLinkToOrg(true)
                          }}
                        >
                          <Building2 className="h-4 w-4 mr-1" />
                          {t("support.people.linkToOrg")}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "workers" && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{t("support.people.tabWorkers")} — {currentOrgName}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {workers.map((worker) => (
                      <div key={worker.id} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">{worker.name}</div>
                          {worker.email && (
                            <div className="text-sm text-muted-foreground">{worker.email}</div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {worker.has_user_account ? (
                            <Badge variant="secondary">{t("support.people.hasAccount")}</Badge>
                          ) : (
                            <Badge variant="outline">{t("support.people.noAccount")}</Badge>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive"
                            onClick={() => unlinkWorker(worker.id)}
                          >
                            {t("support.people.unlink")}
                          </Button>
                        </div>
                      </div>
                    ))}
                    {workers.length === 0 && (
                      <div className="text-center py-4 text-muted-foreground">
                        {t("support.people.noWorkers")}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {availablePersons.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t("support.people.linkWorker")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-2 items-end">
                      <div className="flex-1">
                        <label className="text-sm font-medium">{t("support.people.selectPerson")}</label>
                        <select
                          className="w-full mt-1 bg-background text-foreground border-input rounded px-3 py-2"
                          value={linkWorkerPersonId}
                          onChange={(e) => setLinkWorkerPersonId(e.target.value)}
                        >
                          <option value="">— {t("support.people.selectPerson")} —</option>
                          {availablePersons.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} ({p.national_id || p.email || "—"})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="w-48">
                        <label className="text-sm font-medium">{t("support.people.role")}</label>
                        <Input
                          placeholder={t("support.people.rolePlaceholder")}
                          value={linkWorkerRole}
                          onChange={(e) => setLinkWorkerRole(e.target.value)}
                        />
                      </div>
                      <Button
                        onClick={linkWorker}
                        disabled={!linkWorkerPersonId}
                      >
                        {t("common.add")}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[500px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{t("support.people.addPersonCard")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("support.people.firstName")} *</label>
                  <Input
                    value={newPerson.first_name}
                    onChange={(e) => setNewPerson({ ...newPerson, first_name: e.target.value })}
                    placeholder={t("support.people.firstName")}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">{t("support.people.lastName")} *</label>
                  <Input
                    value={newPerson.last_name}
                    onChange={(e) => setNewPerson({ ...newPerson, last_name: e.target.value })}
                    placeholder={t("support.people.lastName")}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.nationalId")}</label>
                <Input
                  value={newPerson.national_id}
                  onChange={(e) => setNewPerson({ ...newPerson, national_id: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.dateOfBirth")}</label>
                <Input
                  type="date"
                  value={newPerson.date_of_birth}
                  onChange={(e) => setNewPerson({ ...newPerson, date_of_birth: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.email")}</label>
                <Input
                  type="email"
                  value={newPerson.email}
                  onChange={(e) => setNewPerson({ ...newPerson, email: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.phone")}</label>
                <Input
                  value={newPerson.phone}
                  onChange={(e) => setNewPerson({ ...newPerson, phone: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.additionalInfo")}</label>
                <Input
                  value={newPerson.additional_info}
                  onChange={(e) => setNewPerson({ ...newPerson, additional_info: e.target.value })}
                />
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
              <CardTitle>{t("support.people.editPersonCard")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("support.people.firstName")} *</label>
                  <Input
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">{t("support.people.lastName")} *</label>
                  <Input
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.nationalId")}</label>
                <Input
                  value={editForm.national_id}
                  onChange={(e) => setEditForm({ ...editForm, national_id: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.dateOfBirth")}</label>
                <Input
                  type="date"
                  value={editForm.date_of_birth}
                  onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.email")}</label>
                <Input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.phone")}</label>
                <Input
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.additionalInfo")}</label>
                <Input
                  value={editForm.additional_info}
                  onChange={(e) => setEditForm({ ...editForm, additional_info: e.target.value })}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={updatePerson}>{t("common.save")}</Button>
                <Button variant="outline" onClick={() => setEditingPerson(null)}>{t("common.cancel")}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showLinkToOrg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[450px]">
            <CardHeader>
              <CardTitle>{t("support.people.linkToOrg")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">{t("support.people.email")} (Organization)</label>
                {canAdmin ? (
                  <select
                    className="w-full mt-1 bg-background text-foreground border-input rounded px-3 py-2"
                    value={linkOrgId}
                    onChange={(e) => setLinkOrgId(e.target.value)}
                  >
                    <option value="">— {t("selectOrg.select")} —</option>
                    {organizations.map(org => (
                      <option key={org.id} value={org.id}>{org.name}</option>
                    ))}
                  </select>
                ) : (
                  <div className="mt-1 px-3 py-2 bg-secondary rounded text-sm font-medium">
                    {currentOrgName}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm font-medium">{t("support.people.role")}</label>
                <Input
                  placeholder={t("support.people.rolePlaceholder")}
                  value={linkRole}
                  onChange={(e) => setLinkRole(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={linkToOrg}
                  disabled={canAdmin && !linkOrgId}
                >
                  {t("common.add")}
                </Button>
                <Button variant="outline" onClick={() => setShowLinkToOrg(false)}>{t("common.cancel")}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )

  function createPerson() {
    if (!newPerson.first_name || !newPerson.last_name) return
    apiClient.post("/persons/", {
      national_id: newPerson.national_id || null,
      first_name: newPerson.first_name,
      last_name: newPerson.last_name,
      date_of_birth: newPerson.date_of_birth || null,
      email: newPerson.email || null,
      phone: newPerson.phone || null,
      additional_info: newPerson.additional_info || null,
    }).then(() => {
      setShowCreate(false)
      setNewPerson({ national_id: "", first_name: "", last_name: "", date_of_birth: "", email: "", phone: "", additional_info: "" })
      loadData()
    }).catch(console.error)
  }

  function updatePerson() {
    if (!editingPerson) return
    apiClient.patch(`/persons/${editingPerson.id}`, {
      national_id: editForm.national_id || null,
      first_name: editForm.first_name,
      last_name: editForm.last_name,
      date_of_birth: editForm.date_of_birth || null,
      email: editForm.email || null,
      phone: editForm.phone || null,
      additional_info: editForm.additional_info || null,
    }).then(() => {
      setEditingPerson(null)
      loadData()
    }).catch(console.error)
  }

  function deletePerson(personId: string) {
    if (!confirm(t("support.people.confirmDelete"))) return
    apiClient.delete(`/persons/${personId}`).then(() => {
      setSelectedPerson(null)
      loadData()
    }).catch((err: any) => {
      const msg = err?.response?.data?.detail || t("support.people.cannotDelete")
      alert(msg)
    })
  }

  function unlinkOrg(personId: string, tenantId: string) {
    if (!confirm(t("support.people.confirmUnlink"))) return
    apiClient.delete(`/persons/${personId}/organizations/${tenantId}`).then(() => {
      loadData()
      if (selectedPerson?.id === personId) {
        apiClient.get(`/persons/${personId}`).then((res) => {
          setSelectedPerson(res.data)
        }).catch(console.error)
      }
    }).catch(console.error)
  }

  function linkToOrg() {
    if (!selectedPerson) return
    apiClient.post(`/persons/${selectedPerson.id}/organizations`, {
      role: linkRole || null,
    }).then(() => {
      setShowLinkToOrg(false)
      setLinkOrgId("")
      setLinkRole("")
      loadData()
      apiClient.get(`/persons/${selectedPerson.id}`).then((res) => {
        setSelectedPerson(res.data)
      }).catch(console.error)
    }).catch(console.error)
  }

  function linkWorker() {
    if (!linkWorkerPersonId) return
    apiClient.post("/organization/people", {
      person_id: linkWorkerPersonId,
      role: linkWorkerRole || null,
    }).then(() => {
      setLinkWorkerPersonId("")
      setLinkWorkerRole("")
      loadData()
    }).catch(console.error)
  }

  function unlinkWorker(assetId: string) {
    if (!confirm(t("support.people.confirmUnlink"))) return
    apiClient.delete(`/organization/people/${assetId}`).then(() => {
      loadData()
    }).catch(console.error)
  }
}

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(" ")
}