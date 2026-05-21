import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { AlertTriangle, Link2, Unlink, Plus, ExternalLink, Trash2, ArrowRight, ArrowLeft } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface OwnerInfo {
  id: string
  name: string
  email: string
}

interface Division {
  id: string
  name: string
}

interface ProcessListItem {
  id: string
  tenant_id: string
  name: string
  status: string
  confidentiality_need: string
  integrity_need: string
  availability_need: string
  division_id: string | null
  owner: OwnerInfo | null
  asset_count: number
  created_at: string
}

interface BusinessProcessFormData {
  name: string
  description: string
  purpose: string
  inputs: string
  outputs: string
  status: string
  confidentiality_need: string
  integrity_need: string
  availability_need: string
  division_id: string | null
  owner_user_id: string | null
  asset_ids: string[]
}

interface DependencyItem {
  id: string
  depends_on_process_id: string
  dependency_type: string | null
  description: string | null
  created_at: string
  depends_on_process: {
    id: string
    name: string
    status: string
  } | null
}

interface BPEvidence {
  id: string
  title: string
  evidence_type: string
  external_url: string | null
  version: string | null
  owner_name: string | null
  valid_from: string | null
  valid_until: string | null
  review_due_date: string | null
  link_id: string
}

interface EvidenceOption {
  id: string
  title: string
  evidence_type: string
}

type TabType = "info" | "dependencies" | "evidence"

const protectionNeedColors: Record<string, string> = {
  normal: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  high: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  very_high: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-800",
  unknown: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
}

const statusColors: Record<string, string> = {
  active: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  inactive: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
  archived: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-800",
}

const evidenceTypeColors: Record<string, string> = {
  document: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200",
  url: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200",
  note: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200",
}

export default function BusinessProcessesPage() {
  const { t } = useTranslation()
  const { organizations, selectedOrgId } = useAuth()
  const selectedOrgIdRef = useRef(selectedOrgId)
  
  useEffect(() => {
    selectedOrgIdRef.current = selectedOrgId
  }, [selectedOrgId])
  
  const [processes, setProcesses] = useState<ProcessListItem[]>([])
  const [divisions, setDivisions] = useState<Division[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [divisionFilter, setDivisionFilter] = useState<string>("")
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  
  const [formData, setFormData] = useState<BusinessProcessFormData>({
    name: "",
    description: "",
    purpose: "",
    inputs: "",
    outputs: "",
    status: "active",
    confidentiality_need: "normal",
    integrity_need: "normal",
    availability_need: "normal",
    division_id: null,
    owner_user_id: null,
    asset_ids: [],
  })
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [selectedBP, setSelectedBP] = useState<ProcessListItem | null>(null)
  const [showDetail, setShowDetail] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>("info")
  const [dependencies, setDependencies] = useState<{ upstream: DependencyItem[], downstream: DependencyItem[] }>({ upstream: [], downstream: [] })
  const [evidences, setEvidences] = useState<BPEvidence[]>([])
  const [allEvidences, setAllEvidences] = useState<EvidenceOption[]>([])
  const [loadingDeps, setLoadingDeps] = useState(false)
  const [loadingEvidences, setLoadingEvidences] = useState(false)

  const [showAddDependency, setShowAddDependency] = useState(false)
  const [showLinkEvidence, setShowLinkEvidence] = useState(false)
  const [newDepProcessId, setNewDepProcessId] = useState("")
  const [newDepType, setNewDepType] = useState("DATA_FLOW")
  const [newDepDescription, setNewDepDescription] = useState("")
  const [linkEvidenceId, setLinkEvidenceId] = useState("")
  const [searchEvidence, setSearchEvidence] = useState("")

  const fetchDivisions = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      const response = await apiClient.get(`/tenants/${selectedOrgIdRef.current}`)
      if (response.data?.divisions) {
        setDivisions(response.data.divisions)
      }
    } catch (err) {
      console.error("Failed to fetch divisions:", err)
    }
  }

  const fetchProcesses = async () => {
    const orgId = selectedOrgIdRef.current || selectedOrgId
    console.log("fetchProcesses called, org:", orgId)
    if (!orgId) {
      console.log("fetchProcesses: no org id, returning")
      return
    }
    const token = localStorage.getItem("access_token")
    if (!token) {
      console.log("fetchProcesses: no token, returning")
      return
    }
    try {
      console.log("fetchProcesses: fetching...")
      setLoading(true)
      setError(null)
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter
      if (divisionFilter) params.division_id = divisionFilter
      const response = await apiClient.get("/business-processes/", { params })
      console.log("fetchProcesses: got", response.data?.length, "processes")
      setProcesses(response.data)
    } catch (err: any) {
      console.error("fetchProcesses error:", err)
      setError(err.response?.data?.detail || "Failed to load business processes")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!selectedOrgId) return
    fetchDivisions()
    fetchProcesses()
  }, [selectedOrgId, statusFilter, divisionFilter])

  const fetchDependencies = async (bpId: string) => {
    try {
      setLoadingDeps(true)
      const response = await apiClient.get(`/business-processes/${bpId}/dependencies`)
      setDependencies({
        upstream: response.data.dependencies || [],
        downstream: response.data.dependents || [],
      })
    } catch (err) {
      console.error("Failed to fetch dependencies:", err)
    } finally {
      setLoadingDeps(false)
    }
  }

  const fetchBPEvidences = async (bpId: string) => {
    try {
      setLoadingEvidences(true)
      const response = await apiClient.get(`/business-processes/${bpId}/evidences`)
      setEvidences(response.data || [])
    } catch (err) {
      console.error("Failed to fetch BP evidences:", err)
    } finally {
      setLoadingEvidences(false)
    }
  }

  const fetchAllEvidences = async () => {
    try {
      const response = await apiClient.get("/evidences")
      setAllEvidences(response.data || [])
    } catch (err) {
      console.error("Failed to fetch evidences:", err)
    }
  }

  const handleView = async (process: ProcessListItem) => {
    setSelectedBP(process)
    setShowDetail(true)
    setActiveTab("info")
    setDependencies({ upstream: [], downstream: [] })
    setEvidences([])
  }

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab)
    if (selectedBP) {
      if (tab === "dependencies") {
        fetchDependencies(selectedBP.id)
      } else if (tab === "evidence") {
        fetchBPEvidences(selectedBP.id)
        fetchAllEvidences()
      }
    }
  }

  const handleCreate = () => {
    setEditingId(null)
    setFormData({
      name: "",
      description: "",
      purpose: "",
      inputs: "",
      outputs: "",
      status: "active",
      confidentiality_need: "normal",
      integrity_need: "normal",
      availability_need: "normal",
      division_id: null,
      owner_user_id: null,
      asset_ids: [],
    })
    setShowForm(true)
  }

  const handleEdit = (process: ProcessListItem) => {
    setEditingId(process.id)
    setFormData({
      name: process.name,
      description: "",
      purpose: "",
      inputs: "",
      outputs: "",
      status: process.status,
      confidentiality_need: process.confidentiality_need,
      integrity_need: process.integrity_need,
      availability_need: process.availability_need,
      division_id: process.division_id,
      owner_user_id: process.owner?.id || null,
      asset_ids: [],
    })
    setShowForm(true)
  }

  const handleSubmit = async () => {
    try {
      setSaving(true)
      if (editingId) {
        await apiClient.patch(`/business-processes/${editingId}`, formData)
      } else {
        await apiClient.post("/business-processes", formData)
      }
      setShowForm(false)
      fetchProcesses()
    } catch (err: any) {
      console.error("DEBUG handleSubmit error:", err.response?.data || err)
      alert(err.response?.data?.detail || "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/business-processes/${id}`)
      setDeletingId(null)
      fetchProcesses()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete")
    }
  }

  const confirmDelete = (processId: string) => {
    setDeletingId(processId)
  }

  const handleAddDependency = async () => {
    if (!selectedBP || !newDepProcessId) return
    try {
      await apiClient.post(`/business-processes/${selectedBP.id}/dependencies`, {
        depends_on_process_id: newDepProcessId,
        dependency_type: newDepType,
        description: newDepDescription || null,
      })
      setShowAddDependency(false)
      setNewDepProcessId("")
      setNewDepType("DATA_FLOW")
      setNewDepDescription("")
      fetchDependencies(selectedBP.id)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to add dependency")
    }
  }

  const handleDeleteDependency = async (depId: string) => {
    if (!selectedBP) return
    try {
      await apiClient.delete(`/business-processes/${selectedBP.id}/dependencies/${depId}`)
      fetchDependencies(selectedBP.id)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete dependency")
    }
  }

  const handleLinkEvidence = async () => {
    if (!selectedBP || !linkEvidenceId) return
    try {
      await apiClient.post(`/business-processes/${selectedBP.id}/evidence-links`, {
        evidence_id: linkEvidenceId,
      })
      setShowLinkEvidence(false)
      setLinkEvidenceId("")
      setSearchEvidence("")
      fetchBPEvidences(selectedBP.id)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to link evidence")
    }
  }

  const handleUnlinkEvidence = async (linkId: string) => {
    if (!selectedBP) return
    try {
      await apiClient.delete(`/business-processes/${selectedBP.id}/evidence-links/${linkId}`)
      fetchBPEvidences(selectedBP.id)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to unlink evidence")
    }
  }

  const getDivisionName = (divisionId: string | null) => {
    if (!divisionId) return null
    const division = divisions.find(d => d.id === divisionId)
    return division?.name || null
  }

  const filteredProcesses = processes.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  const availableProcessesForDep = processes.filter(
    p => p.id !== selectedBP?.id && !dependencies.upstream.some(d => d.depends_on_process_id === p.id)
  )

  const filteredAllEvidences = allEvidences.filter(e =>
    e.title.toLowerCase().includes(searchEvidence.toLowerCase()) &&
    !evidences.some(ev => ev.id === e.id)
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">{t("common.loading")}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold">{t("businessProcesses.title")}</h1>
          {selectedOrgId && (
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 text-base px-3 py-1">
              {organizations.find(o => o.id === selectedOrgId)?.name || t("common.unknownOrg")}
            </Badge>
          )}
        </div>
        <Button onClick={handleCreate}>{t("common.add")}</Button>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-4">
        <Input
          placeholder={t("common.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <select
          className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">{t("common.allStatuses")}</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="archived">Archived</option>
        </select>
        {divisions.length > 0 && (
          <select
            className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={divisionFilter}
            onChange={(e) => setDivisionFilter(e.target.value)}
          >
            <option value="">{t("common.allDivisions")}</option>
            {divisions.map((div) => (
              <option key={div.id} value={div.id}>
                {div.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {filteredProcesses.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{t("businessProcesses.noData")}</p>
          </CardContent>
        </Card>
      )}

      {filteredProcesses.length > 0 && (
        <div className="space-y-4">
          {filteredProcesses.map((process) => (
            <Card key={process.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl">{process.name}</CardTitle>
                    {process.owner && (
                      <p className="text-base text-muted-foreground">
                        {t("roles.process_owner.name")}: {process.owner.name}
                      </p>
                    )}
                    {process.division_id && getDivisionName(process.division_id) && (
                      <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200 text-base">
                        {getDivisionName(process.division_id)}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`${statusColors[process.status] || statusColors.unknown} text-base`}
                    >
                      {t(`common.${process.status}`) || process.status}
                    </Badge>
                    <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 dark:text-blue-200 text-base">
                      {process.asset_count} {t("nav.assets")}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 mb-4">
                  <div className="text-base">
                    <span className="text-muted-foreground">C: </span>
                    <Badge
                      variant="outline"
                      className={`${protectionNeedColors[process.confidentiality_need]} text-base`}
                    >
                      {t(`protectionNeed.${process.confidentiality_need}`) || process.confidentiality_need}
                    </Badge>
                  </div>
                  <div className="text-base">
                    <span className="text-muted-foreground">I: </span>
                    <Badge
                      variant="outline"
                      className={`${protectionNeedColors[process.integrity_need]} text-base`}
                    >
                      {t(`protectionNeed.${process.integrity_need}`) || process.integrity_need}
                    </Badge>
                  </div>
                  <div className="text-base">
                    <span className="text-muted-foreground">A: </span>
                    <Badge
                      variant="outline"
                      className={`${protectionNeedColors[process.availability_need]} text-base`}
                    >
                      {t(`protectionNeed.${process.availability_need}`) || process.availability_need}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleView(process)}>
                    {t("common.view")}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleEdit(process)}>
                    {t("common.edit")}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => confirmDelete(process.id)}
                    className="text-destructive"
                  >
                    {t("common.delete")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>{editingId ? t("common.edit") : t("common.add")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">{t("common.name")} *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder={t("businessProcesses.namePlaceholder")}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("common.description")}</label>
                <textarea
                  value={formData.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, description: e.target.value })}
                  placeholder={t("businessProcesses.descPlaceholder")}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("common.purpose")}</label>
                <textarea
                  value={formData.purpose}
                  onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                  placeholder={t("businessProcesses.purposePlaceholder")}
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("common.inputs")}</label>
                  <textarea
                    value={formData.inputs}
                    onChange={(e) => setFormData({ ...formData, inputs: e.target.value })}
                    placeholder={t("businessProcesses.inputsPlaceholder")}
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">{t("common.outputs")}</label>
                  <textarea
                    value={formData.outputs}
                    onChange={(e) => setFormData({ ...formData, outputs: e.target.value })}
                    placeholder={t("businessProcesses.outputsPlaceholder")}
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("common.division")}</label>
                <select
                  value={formData.division_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, division_id: e.target.value || null })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">{t("businessProcesses.noDivision")}</option>
                  {divisions.map((div) => (
                    <option key={div.id} value={div.id}>
                      {div.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">{t("common.status")}</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="active">{t("common.active")}</option>
                  <option value="inactive">{t("common.inactive")}</option>
                  <option value="archived">{t("common.archived")}</option>
                </select>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("common.confidentiality")}</label>
                  <select
                    value={formData.confidentiality_need}
                    onChange={(e) =>
                      setFormData({ ...formData, confidentiality_need: e.target.value })
                    }
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="normal">{t("protectionNeed.normal") || "Normal"}</option>
                    <option value="high">{t("protectionNeed.high") || "High"}</option>
                    <option value="very_high">{t("protectionNeed.very_high") || "Very High"}</option>
                    <option value="unknown">{t("protectionNeed.unknown") || "Unknown"}</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">{t("common.integrity")}</label>
                  <select
                    value={formData.integrity_need}
                    onChange={(e) =>
                      setFormData({ ...formData, integrity_need: e.target.value })
                    }
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="normal">{t("protectionNeed.normal") || "Normal"}</option>
                    <option value="high">{t("protectionNeed.high") || "High"}</option>
                    <option value="very_high">{t("protectionNeed.very_high") || "Very High"}</option>
                    <option value="unknown">{t("protectionNeed.unknown") || "Unknown"}</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">{t("common.availability")}</label>
                  <select
                    value={formData.availability_need}
                    onChange={(e) =>
                      setFormData({ ...formData, availability_need: e.target.value })
                    }
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="normal">{t("protectionNeed.normal") || "Normal"}</option>
                    <option value="high">{t("protectionNeed.high") || "High"}</option>
                    <option value="very_high">{t("protectionNeed.very_high") || "Very High"}</option>
                    <option value="unknown">{t("protectionNeed.unknown") || "Unknown"}</option>
                  </select>
                </div>
              </div>
              <div className="flex items-center justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowForm(false)}>
                  {t("common.cancel")}
                </Button>
                <Button onClick={handleSubmit} disabled={saving || !formData.name}>
                  {saving ? t("common.saving") : t("common.save")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showDetail && selectedBP && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-2xl">{selectedBP.name}</CardTitle>
                <Button variant="ghost" onClick={() => setShowDetail(false)}>✕</Button>
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleTabChange("info")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === "info"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  {t("common.info")}
                </button>
                <button
                  onClick={() => handleTabChange("dependencies")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === "dependencies"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  {t("businessProcesses.dependencies") || "Dependencies"}
                </button>
                <button
                  onClick={() => handleTabChange("evidence")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === "evidence"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  {t("evidences.title") || "Evidence"}
                </button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              {activeTab === "info" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">{t("common.status")}</label>
                      <p className="text-sm mt-1">
                        <Badge variant="outline" className={statusColors[selectedBP.status]}>
                          {t(`common.${selectedBP.status}`) || selectedBP.status}
                        </Badge>
                      </p>
                    </div>
                    {selectedBP.owner && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">{t("roles.process_owner.name")}</label>
                        <p className="text-sm mt-1">{selectedBP.owner.name}</p>
                      </div>
                    )}
                    {selectedBP.division_id && getDivisionName(selectedBP.division_id) && (
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">{t("common.division")}</label>
                        <p className="text-sm mt-1">{getDivisionName(selectedBP.division_id)}</p>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">{t("businessProcesses.protectionNeeds") || "Protection Needs"}</label>
                    <div className="flex gap-4 mt-2">
                      <div>
                        <span className="text-sm">{t("common.confidentiality")}: </span>
                        <Badge variant="outline" className={protectionNeedColors[selectedBP.confidentiality_need]}>
                          {t(`protectionNeed.${selectedBP.confidentiality_need}`) || selectedBP.confidentiality_need}
                        </Badge>
                      </div>
                      <div>
                        <span className="text-sm">{t("common.integrity")}: </span>
                        <Badge variant="outline" className={protectionNeedColors[selectedBP.integrity_need]}>
                          {t(`protectionNeed.${selectedBP.integrity_need}`) || selectedBP.integrity_need}
                        </Badge>
                      </div>
                      <div>
                        <span className="text-sm">{t("common.availability")}: </span>
                        <Badge variant="outline" className={protectionNeedColors[selectedBP.availability_need]}>
                          {t(`protectionNeed.${selectedBP.availability_need}`) || selectedBP.availability_need}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">{t("nav.assets")}</label>
                    <p className="text-sm mt-1">{selectedBP.asset_count} {t("nav.assets")}</p>
                  </div>
                </div>
              )}

              {activeTab === "dependencies" && (
                <div className="space-y-6">
                  {loadingDeps ? (
                    <p className="text-muted-foreground">{t("common.loading")}</p>
                  ) : (
                    <>
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <ArrowRight className="h-4 w-4" />
                            {t("businessProcesses.upstream") || "Upstream Dependencies"} ({dependencies.upstream.length})
                          </h3>
                          <Button size="sm" variant="outline" onClick={() => setShowAddDependency(true)}>
                            <Plus className="h-4 w-4 mr-1" />
                            {t("common.add")}
                          </Button>
                        </div>
                        {dependencies.upstream.length === 0 ? (
                          <p className="text-sm text-muted-foreground py-4">
                            {t("businessProcesses.noUpstream") || "No upstream dependencies"}
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {dependencies.upstream.map((dep) => (
                              <div key={dep.id} className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                  <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900">
                                    {dep.dependency_type || "DATA_FLOW"}
                                  </Badge>
                                  <div>
                                    <p className="font-medium">{dep.depends_on_process?.name || "Unknown"}</p>
                                    {dep.description && (
                                      <p className="text-sm text-muted-foreground">{dep.description}</p>
                                    )}
                                  </div>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-destructive"
                                  onClick={() => handleDeleteDependency(dep.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      <div>
                        <h3 className="text-lg font-semibold flex items-center gap-2 mb-3">
                          <ArrowLeft className="h-4 w-4" />
                          {t("businessProcesses.downstream") || "Downstream Dependents"} ({dependencies.downstream.length})
                        </h3>
                        {dependencies.downstream.length === 0 ? (
                          <p className="text-sm text-muted-foreground py-4">
                            {t("businessProcesses.noDownstream") || "No downstream dependents"}
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {dependencies.downstream.map((dep) => (
                              <div key={dep.id} className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                  <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900">
                                    {dep.dependency_type || "DATA_FLOW"}
                                  </Badge>
                                  <div>
                                    <p className="font-medium">{dep.depends_on_process?.name || "Unknown"}</p>
                                    {dep.description && (
                                      <p className="text-sm text-muted-foreground">{dep.description}</p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {activeTab === "evidence" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">{t("evidences.linked") || "Linked Evidence"} ({evidences.length})</h3>
                    <Button size="sm" variant="outline" onClick={() => {
                      fetchAllEvidences()
                      setShowLinkEvidence(true)
                    }}>
                      <Link2 className="h-4 w-4 mr-1" />
                      {t("evidences.linkExisting") || "Link Existing"}
                    </Button>
                  </div>

                  {loadingEvidences ? (
                    <p className="text-muted-foreground">{t("common.loading")}</p>
                  ) : evidences.length === 0 ? (
                    <div className="text-center py-8 border rounded-lg bg-muted/20">
                      <p className="text-muted-foreground mb-2">{t("evidences.noLinked") || "No evidence linked to this process"}</p>
                      <p className="text-sm text-muted-foreground">
                        {t("evidences.clickToLink") || "Click 'Link Existing' to attach evidence from the Evidence register."}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {evidences.map((ev) => (
                        <div key={ev.link_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex items-center gap-3">
                            <Badge variant="outline" className={evidenceTypeColors[ev.evidence_type] || "bg-gray-100"}>
                              {ev.evidence_type}
                            </Badge>
                            <div>
                              <p className="font-medium">{ev.title}</p>
                              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                {ev.owner_name && <span>{ev.owner_name}</span>}
                                {ev.external_url && (
                                  <a
                                    href={ev.external_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1 text-blue-600 hover:underline"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                    URL
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive"
                            onClick={() => handleUnlinkEvidence(ev.link_id)}
                          >
                            <Unlink className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <Dialog open={!!deletingId} onOpenChange={(open) => !open && setDeletingId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
              {t("businessProcesses.deleteConfirmTitle") || "Warning!"}
            </DialogTitle>
            <DialogDescription>
              {t("businessProcesses.deleteConfirmDesc") || "Are you sure you want to delete this business process? This action cannot be undone."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingId(null)}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={() => deletingId && handleDelete(deletingId)}>
              {t("common.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAddDependency} onOpenChange={(open) => {
        setShowAddDependency(open)
        if (!open) {
          setNewDepProcessId("")
          setNewDepType("DATA_FLOW")
          setNewDepDescription("")
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("businessProcesses.addDependency") || "Add Dependency"}</DialogTitle>
            <DialogDescription>
              {t("businessProcesses.addDependencyDesc") || "Select a process that this business process depends on."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t("businessProcesses.dependsOn") || "Depends on"} *</label>
              <select
                value={newDepProcessId}
                onChange={(e) => setNewDepProcessId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="">{t("common.select") || "Select..."}</option>
                {availableProcessesForDep.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">{t("common.type") || "Type"}</label>
              <select
                value={newDepType}
                onChange={(e) => setNewDepType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="DATA_FLOW">DATA_FLOW</option>
                <option value="OPERATIONAL_TRIGGER">OPERATIONAL_TRIGGER</option>
                <option value="INFORMATION_EXCHANGE">INFORMATION_EXCHANGE</option>
                <option value="SUPPORTING_SERVICE">SUPPORTING_SERVICE</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">{t("common.description")}</label>
              <textarea
                value={newDepDescription}
                onChange={(e) => setNewDepDescription(e.target.value)}
                placeholder={t("businessProcesses.depDescriptionPlaceholder") || "Description of dependency..."}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDependency(false)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={handleAddDependency} disabled={!newDepProcessId}>
              {t("common.add")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showLinkEvidence} onOpenChange={(open) => {
        setShowLinkEvidence(open)
        if (!open) {
          setLinkEvidenceId("")
          setSearchEvidence("")
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("evidences.linkToProcess") || "Link Evidence to Process"}</DialogTitle>
            <DialogDescription>
              {t("evidences.selectEvidence") || "Select an evidence item to link to this business process."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t("common.search")}</label>
              <Input
                value={searchEvidence}
                onChange={(e) => setSearchEvidence(e.target.value)}
                placeholder={t("evidences.searchPlaceholder") || "Search evidence..."}
                className="mt-1"
              />
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {filteredAllEvidences.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4">
                  {t("evidences.noAvailable") || "No evidence items available"}
                </p>
              ) : (
                filteredAllEvidences.map((ev) => (
                  <div
                    key={ev.id}
                    className={`p-3 border rounded-lg cursor-pointer hover:bg-muted ${
                      linkEvidenceId === ev.id ? "border-primary bg-primary/5" : ""
                    }`}
                    onClick={() => setLinkEvidenceId(ev.id)}
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className={evidenceTypeColors[ev.evidence_type] || "bg-gray-100"}>
                        {ev.evidence_type}
                      </Badge>
                      <span className="font-medium">{ev.title}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLinkEvidence(false)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={handleLinkEvidence} disabled={!linkEvidenceId}>
              {t("common.add")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}