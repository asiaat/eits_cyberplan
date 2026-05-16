import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { AlertTriangle, Search, ChevronDown, ChevronRight, Unlink, Link2 } from "lucide-react"

interface OwnerInfo {
  id: string
  name: string
  email: string
}

interface LinkedProcess {
  id: string
  name: string
  status: string
}

interface AssetListItem {
  id: string
  tenant_id: string
  name: string
  asset_type: string
  criticality: string
  confidentiality_need: string
  integrity_need: string
  availability_need: string
  lifecycle_status: string
  owner_user_id: string | null
  person_id: string | null
  owner: OwnerInfo | null
  linked_process_count: number
  linked_processes: LinkedProcess[]
  can_manage_links: boolean
  created_at: string
}

interface AssetFormData {
  name: string
  asset_type: string
  description: string
  criticality: string
  confidentiality_need: string
  integrity_need: string
  availability_need: string
  lifecycle_status: string
  owner_user_id: string | null
  person_id: string | null
}

interface User {
  id: string
  name: string
  email: string
}

interface Person {
  id: string
  name: string
}

interface BusinessProcessOption {
  id: string
  name: string
  status: string
}

const protectionNeedColors: Record<string, string> = {
  normal: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  high: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  very_high: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-800",
  unknown: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
}

const criticalityColors: Record<string, string> = {
  low: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  normal: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-800",
  high: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  critical: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-800",
}

const statusColors: Record<string, string> = {
  active: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  inactive: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700",
  deprecated: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  retired: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-800",
}

export default function AssetsPage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const selectedOrgIdRef = useRef(selectedOrgId)
  const [assets, setAssets] = useState<AssetListItem[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<AssetFormData>({
    name: "",
    asset_type: "information_asset",
    description: "",
    criticality: "normal",
    confidentiality_need: "normal",
    integrity_need: "normal",
    availability_need: "normal",
    lifecycle_status: "active",
    owner_user_id: null,
    person_id: null,
  })
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({})
  const [linkingProcess, setLinkingProcess] = useState(false)
  const [showAddProcess, setShowAddProcess] = useState(false)
  const [selectedProcess, setSelectedProcess] = useState<string | null>(null)
  const [loadingProcesses, setLoadingProcesses] = useState(false)
  const [unlinkedProcesses, setUnlinkedProcesses] = useState<BusinessProcessOption[]>([])

  useEffect(() => { selectedOrgIdRef.current = selectedOrgId }, [selectedOrgId])

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!selectedOrgIdRef.current || !token) return
    fetchUsers()
    fetchPersons()
    fetchAssets()
  }, [selectedOrgId, typeFilter, statusFilter, search])

  const fetchUsers = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      const response = await apiClient.get("/users/")
      const usersData = response.data?.users || response.data || []
      setUsers(Array.isArray(usersData) ? usersData : [])
    } catch (err) {
      console.error("Failed to fetch users:", err)
      setUsers([])
    }
  }

  const fetchPersons = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      const response = await apiClient.get("/persons/")
      const personsData = response.data || []
      setPersons(Array.isArray(personsData) ? personsData : [])
    } catch (err) {
      console.error("Failed to fetch persons:", err)
      setPersons([])
    }
  }

  const fetchAssets = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      setLoading(true)
      setError(null)
      const params: Record<string, string> = {}
      if (typeFilter) params.type = typeFilter
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const response = await apiClient.get("/assets/", { params })
      setAssets(response.data || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load assets")
    } finally {
      setLoading(false)
    }
  }

  const toggleExpanded = (assetId: string) => {
    setExpandedCards(prev => ({
      ...prev,
      [assetId]: !prev[assetId]
    }))
  }

  const handleCreate = () => {
    setEditingId(null)
    setFormData({
      name: "",
      asset_type: "information_asset",
      description: "",
      criticality: "normal",
      confidentiality_need: "normal",
      integrity_need: "normal",
      availability_need: "normal",
      lifecycle_status: "active",
      owner_user_id: null,
      person_id: null,
    })
    setShowForm(true)
  }

  const handleEdit = (asset: AssetListItem) => {
    setEditingId(asset.id)
    setFormData({
      name: asset.name,
      asset_type: asset.asset_type,
      description: "",
      criticality: asset.criticality,
      confidentiality_need: asset.confidentiality_need,
      integrity_need: asset.integrity_need,
      availability_need: asset.availability_need,
      lifecycle_status: asset.lifecycle_status,
      owner_user_id: asset.owner_user_id,
      person_id: asset.person_id,
    })
    setShowForm(true)
  }

  const handleSubmit = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      setSaving(true)
      const payload = {
        ...formData,
        owner_user_id: formData.owner_user_id || null,
        person_id: formData.person_id || null,
      }
      if (editingId) {
        await apiClient.patch(`/assets/${editingId}/`, payload)
      } else {
        await apiClient.post("/assets/", payload)
      }
      setShowForm(false)
      fetchAssets()
    } catch (err: any) {
      console.error("DEBUG handleSubmit error:", err.response?.data || err)
      alert(err.response?.data?.detail || "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      await apiClient.delete(`/assets/${id}/`)
      setDeletingId(null)
      setDeleteError(null)
      fetchAssets()
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to delete"
      setDeleteError(msg)
    }
  }

  const confirmDelete = (assetId: string) => {
    setDeletingId(assetId)
    setDeleteError(null)
  }

  const handleDeleteCancel = () => {
    setDeletingId(null)
    setDeleteError(null)
  }

  const fetchUnlinkedProcesses = async (assetId: string) => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      setLoadingProcesses(true)
      const response = await apiClient.get(`/assets/${assetId}/unlinked-processes`)
      setUnlinkedProcesses(response.data || [])
      setSelectedProcess("")
    } catch (err) {
      console.error("Failed to fetch unlinked processes:", err)
      setUnlinkedProcesses([])
    } finally {
      setLoadingProcesses(false)
    }
  }

  const handleLinkProcess = async (assetId: string) => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    if (!selectedProcess) return
    try {
      setLinkingProcess(true)
      await apiClient.post(`/assets/${assetId}/processes/${selectedProcess}`)
      setShowAddProcess(false)
      setSelectedProcess("")
      setUnlinkedProcesses([])
      fetchAssets()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to link process")
    } finally {
      setLinkingProcess(false)
    }
  }

  const handleUnlinkProcess = async (assetId: string, processId: string) => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      await apiClient.delete(`/assets/${assetId}/processes/${processId}`)
      fetchAssets()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to unlink process")
    }
  }

  const openAddProcess = (assetId: string) => {
    fetchUnlinkedProcesses(assetId)
    setShowAddProcess(true)
  }

  const closeAddProcess = () => {
    setShowAddProcess(false)
    setSelectedProcess("")
    setUnlinkedProcesses([])
  }

  const getAssetForDialog = () => {
    if (!deletingId) return null
    return assets.find(a => a.id === deletingId) || null
  }

  const getEditingAsset = () => {
    if (!editingId) return null
    return assets.find(a => a.id === editingId) || null
  }

  const filteredAssets = assets.filter((a) =>
    a.name.toLowerCase().includes(search.toLowerCase())
  )

  const assetTypes = [
    { value: "information_asset", label: t("assets.types.information_asset") },
    { value: "software", label: t("assets.types.software") },
    { value: "hardware", label: t("assets.types.hardware") },
    { value: "service", label: t("assets.types.service") },
    { value: "data", label: t("assets.types.data") },
    { value: "other", label: t("assets.types.other") },
  ]

  const criticalityLevels = [
    { value: "low", label: t("assets.criticalityLevels.low") },
    { value: "normal", label: t("assets.criticalityLevels.normal") },
    { value: "high", label: t("assets.criticalityLevels.high") },
    { value: "critical", label: t("assets.criticalityLevels.critical") },
  ]

  const statusLevels = [
    { value: "active", label: t("assets.statusLevels.active") },
    { value: "inactive", label: t("assets.statusLevels.inactive") },
    { value: "deprecated", label: t("assets.statusLevels.deprecated") },
    { value: "retired", label: t("assets.statusLevels.retired") },
  ]

  const protectionLevels = [
    { value: "normal", label: t("protectionNeed.normal") },
    { value: "high", label: t("protectionNeed.high") },
    { value: "very_high", label: t("protectionNeed.very_high") },
    { value: "unknown", label: t("protectionNeed.unknown") },
  ]

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
        <h1 className="text-3xl font-bold">{t("assets.title")}</h1>
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
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("common.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">{t("assets.type") || "All types"}</option>
          {assetTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <select
          className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">{t("assets.status") || "All statuses"}</option>
          {statusLevels.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
      </div>

      {filteredAssets.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{t("assets.noData")}</p>
          </CardContent>
        </Card>
      )}

      {filteredAssets.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAssets.map((asset) => (
            <Card key={asset.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-xl">{asset.name}</CardTitle>
                    <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200 text-base">
                      {t(`assets.types.${asset.asset_type}`) || asset.asset_type}
                    </Badge>
                  </div>
                  <Badge
                    variant="outline"
                    className={`${statusColors[asset.lifecycle_status] || statusColors.inactive} text-base`}
                  >
                    {t(`assets.statusLevels.${asset.lifecycle_status}`) || asset.lifecycle_status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`${criticalityColors[asset.criticality] || criticalityColors.normal} text-base`}
                    >
                      {t(`assets.criticalityLevels.${asset.criticality}`) || asset.criticality}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <div className="text-sm">
                      <span className="text-muted-foreground">C: </span>
                      <Badge
                        variant="outline"
                        className={`${protectionNeedColors[asset.confidentiality_need]} text-sm`}
                      >
                        {t(`protectionNeed.${asset.confidentiality_need}`) || asset.confidentiality_need}
                      </Badge>
                    </div>
                    <div className="text-sm">
                      <span className="text-muted-foreground">I: </span>
                      <Badge
                        variant="outline"
                        className={`${protectionNeedColors[asset.integrity_need]} text-sm`}
                      >
                        {t(`protectionNeed.${asset.integrity_need}`) || asset.integrity_need}
                      </Badge>
                    </div>
                    <div className="text-sm">
                      <span className="text-muted-foreground">A: </span>
                      <Badge
                        variant="outline"
                        className={`${protectionNeedColors[asset.availability_need]} text-sm`}
                      >
                        {t(`protectionNeed.${asset.availability_need}`) || asset.availability_need}
                      </Badge>
                    </div>
                  </div>
                  {asset.owner && (
                    <p className="text-sm text-muted-foreground">
                      {t("assets.owner")}: {asset.owner.name}
                    </p>
                  )}

                  {asset.linked_process_count > 0 ? (
                    <div className="border-t pt-2 mt-2">
                      <button
                        onClick={() => toggleExpanded(asset.id)}
                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {expandedCards[asset.id] ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                        <span>{asset.linked_process_count} {t("assets.linkedProcesses")}</span>
                      </button>
                      {expandedCards[asset.id] && (
                        <div className="mt-2 space-y-1 pl-5">
                          {asset.linked_processes.map((proc) => (
                            <div key={proc.id} className="flex items-center justify-between text-sm">
                              <span className="flex items-center gap-1">
                                {proc.name}
                                <Badge variant="outline" className={`${statusColors[proc.status]} text-xs`}>
                                  {t(`common.${proc.status}`) || proc.status}
                                </Badge>
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      {t("assets.noLinkedProcesses")}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-4">
                  <Button variant="outline" size="sm" onClick={() => handleEdit(asset)}>
                    {t("common.edit")}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => confirmDelete(asset.id)}
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
                <label className="text-sm font-medium">{t("assets.name")} *</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter asset name"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.type")} *</label>
                <select
                  value={formData.asset_type}
                  onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {assetTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.description")}</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the asset"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.criticality")}</label>
                <select
                  value={formData.criticality}
                  onChange={(e) => setFormData({ ...formData, criticality: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {criticalityLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">{t("common.confidentiality")}</label>
                  <select
                    value={formData.confidentiality_need}
                    onChange={(e) => setFormData({ ...formData, confidentiality_need: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {protectionLevels.map((level) => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">{t("common.integrity")}</label>
                  <select
                    value={formData.integrity_need}
                    onChange={(e) => setFormData({ ...formData, integrity_need: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {protectionLevels.map((level) => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">{t("common.availability")}</label>
                  <select
                    value={formData.availability_need}
                    onChange={(e) => setFormData({ ...formData, availability_need: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {protectionLevels.map((level) => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.status")}</label>
                <select
                  value={formData.lifecycle_status}
                  onChange={(e) => setFormData({ ...formData, lifecycle_status: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {statusLevels.map((status) => (
                    <option key={status.value} value={status.value}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.owner")}</label>
                <select
                  value={formData.owner_user_id || ""}
                  onChange={(e) => setFormData({ ...formData, owner_user_id: e.target.value || null })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">— {t("common.none")} —</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} ({user.email})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.person")}</label>
                <select
                  value={formData.person_id || ""}
                  onChange={(e) => setFormData({ ...formData, person_id: e.target.value || null })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">— {t("common.none")} —</option>
                  {persons.map((person) => (
                    <option key={person.id} value={person.id}>
                      {person.name}
                    </option>
                  ))}
                </select>
              </div>

              {editingId && getEditingAsset() && (
                <div className="border-t pt-4 mt-4">
                  <h4 className="text-sm font-medium mb-2">{t("assets.linkedProcessesSection")}</h4>

                  {getEditingAsset()!.linked_processes.length > 0 ? (
                    <div className="space-y-2 mb-3">
                      {getEditingAsset()!.linked_processes.map((proc) => (
                        <div key={proc.id} className="flex items-center justify-between p-2 bg-secondary rounded">
                          <span className="flex items-center gap-2">
                            {proc.name}
                            <Badge variant="outline" className={`${statusColors[proc.status]} text-xs`}>
                              {t(`common.${proc.status}`) || proc.status}
                            </Badge>
                          </span>
                          {getEditingAsset()!.can_manage_links && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUnlinkProcess(editingId, proc.id)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Unlink className="h-4 w-4 mr-1" />
                              {t("assets.unlink")}
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground mb-3">{t("assets.noLinkedProcesses")}</p>
                  )}

                  {getEditingAsset()!.can_manage_links && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openAddProcess(editingId)}
                    >
                      <Link2 className="h-4 w-4 mr-1" />
                      {t("assets.addToProcess")}
                    </Button>
                  )}
                </div>
              )}

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
              {t("assets.confirmDeleteTitle")}
            </DialogTitle>
            <DialogDescription>
              <span className="font-semibold block mb-2">
                {t("assets.confirmDeleteSubtitle")}
              </span>
              {getAssetForDialog()?.linked_process_count && getAssetForDialog()!.linked_process_count > 0 ? (
                <div>
                  <p className="mb-2">{t("assets.cannotDeleteLinked")}</p>
                  <p className="text-sm font-medium mb-1">{t("assets.linkedProcesses")}:</p>
                  <ul className="list-disc pl-5 text-sm">
                    {getAssetForDialog()!.linked_processes.map((proc) => (
                      <li key={proc.id}>
                        {proc.name} ({t(`common.${proc.status}`) || proc.status})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : deleteError ? (
                <span className="text-destructive">{deleteError}</span>
              ) : (
                <span>{t("assets.confirmDelete")}</span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={handleDeleteCancel}>
              {t("common.cancel")}
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingId && handleDelete(deletingId)}
              disabled={!!getAssetForDialog()?.linked_process_count && getAssetForDialog()!.linked_process_count > 0}
            >
              {t("common.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showAddProcess} onOpenChange={(open) => !open && closeAddProcess()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("assets.addToProcess")}</DialogTitle>
            <DialogDescription>
              {loadingProcesses ? (
                <span>{t("common.loading")}</span>
              ) : unlinkedProcesses.length === 0 ? (
                <span>{t("assets.noData") || "No available processes to link."}</span>
              ) : (
                <span>{t("assets.selectProcess")}</span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={selectedProcess ?? ""}
              onChange={(e) => setSelectedProcess(e.target.value)}
              disabled={loadingProcesses || unlinkedProcesses.length === 0}
            >
              <option value="">— {t("assets.selectProcess")} —</option>
              {unlinkedProcesses.map((proc) => (
                <option key={proc.id} value={proc.id}>
                  {proc.name} ({t(`common.${proc.status}`) || proc.status})
                </option>
              ))}
            </select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeAddProcess}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={() => editingId && handleLinkProcess(editingId)}
              disabled={!selectedProcess || linkingProcess || unlinkedProcesses.length === 0}
            >
              {linkingProcess ? t("common.saving") : t("assets.link")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}