import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { AlertTriangle } from "lucide-react"
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

export default function BusinessProcessesPage() {
  const { t } = useTranslation()
  const { organizations, selectedOrgId } = useAuth()
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

  useEffect(() => {
    fetchDivisions()
    fetchProcesses()
  }, [selectedOrgId])

  const fetchDivisions = async () => {
    if (!selectedOrgId) return
    try {
      const response = await apiClient.get(`/tenants/${selectedOrgId}`)
      if (response.data?.divisions) {
        setDivisions(response.data.divisions)
      }
    } catch (err) {
      console.error("Failed to fetch divisions:", err)
    }
  }

  const fetchProcesses = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter
      if (divisionFilter) params.division_id = divisionFilter
      const response = await apiClient.get("/business-processes", { params })
      setProcesses(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load business processes")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcesses()
  }, [statusFilter, divisionFilter])

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
      console.log("DEBUG handleSubmit formData:", formData)
      console.log("DEBUG division_id value:", formData.division_id)
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

  const handleDeleteConfirm = () => {
    if (deletingId) {
      handleDelete(deletingId)
    }
  }

  const handleDeleteCancel = () => {
    setDeletingId(null)
  }

  const getDivisionName = (divisionId: string | null) => {
    if (!divisionId) return null
    const division = divisions.find(d => d.id === divisionId)
    return division?.name || divisionId
  }

  const filteredProcesses = processes.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
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
              {organizations.find(o => o.id === selectedOrgId)?.name || "Unknown Org"}
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
          <option value="">All statuses</option>
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
            <option value="">{t("organization.divisions") || "All divisions"}</option>
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
                    {process.division_id && (
                      <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200 text-base">
                        {getDivisionName(process.division_id)}
                      </Badge>
                    )}
                    <Badge variant="outline" className="bg-gray-50 dark:bg-gray-800 dark:text-gray-200 text-base">
                      {organizations.find(o => o.id === process.tenant_id)?.name || process.tenant_id}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`${statusColors[process.status] || statusColors.unknown} text-base`}
                    >
                      {process.status}
                    </Badge>
                    <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 dark:text-blue-200 text-base">
                      {process.asset_count} assets
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
                      {process.confidentiality_need}
                    </Badge>
                  </div>
                  <div className="text-base">
                    <span className="text-muted-foreground">I: </span>
                    <Badge
                      variant="outline"
                      className={`${protectionNeedColors[process.integrity_need]} text-base`}
                    >
                      {process.integrity_need}
                    </Badge>
                  </div>
                  <div className="text-base">
                    <span className="text-muted-foreground">A: </span>
                    <Badge
                      variant="outline"
                      className={`${protectionNeedColors[process.availability_need]} text-base`}
                    >
                      {process.availability_need}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-2">
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
                <label className="text-sm font-medium">Name *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Process name"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Description"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Purpose</label>
                <textarea
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.purpose}
                  onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                  placeholder="Purpose of the process"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Inputs</label>
                  <Input
                    value={formData.inputs}
                    onChange={(e) => setFormData({ ...formData, inputs: e.target.value })}
                    placeholder="Process inputs"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Outputs</label>
                  <Input
                    value={formData.outputs}
                    onChange={(e) => setFormData({ ...formData, outputs: e.target.value })}
                    placeholder="Process outputs"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Division</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.division_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, division_id: e.target.value || null })
                  }
                >
                  <option value="">No division</option>
                  {divisions.map((div) => (
                    <option key={div.id} value={div.id}>
                      {div.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">Confidentiality</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.confidentiality_need}
                    onChange={(e) =>
                      setFormData({ ...formData, confidentiality_need: e.target.value })
                    }
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Integrity</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.integrity_need}
                    onChange={(e) =>
                      setFormData({ ...formData, integrity_need: e.target.value })
                    }
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Availability</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.availability_need}
                    onChange={(e) =>
                      setFormData({ ...formData, availability_need: e.target.value })
                    }
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                    <option value="unknown">Unknown</option>
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

      <Dialog open={!!deletingId} onOpenChange={(open) => !open && handleDeleteCancel()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
              {t("businessProcesses.deleteConfirmTitle") || "Warning!"}
            </DialogTitle>
            <DialogDescription>
              <span className="font-semibold block mb-1">
                {t("businessProcesses.deleteConfirmSubtitle") || "Delete Business Process"}
              </span>
              {t("businessProcesses.deleteConfirmDesc") || "Are you sure you want to delete this business process? This action cannot be undone."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleDeleteCancel}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              {t("common.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}