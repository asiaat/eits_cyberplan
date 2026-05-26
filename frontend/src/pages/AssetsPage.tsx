import { useState, useEffect, useRef, useMemo } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { AlertTriangle, Search, ChevronDown, ChevronRight, Unlink, Link2, LayoutGrid, List, ArrowUpDown, ArrowUp, ArrowDown, BookOpen, Loader2, X, Upload } from "lucide-react"
import { ErrorDialog } from "@/components/ui/error-dialog"
import { WarningDialog } from "@/components/ui/warning-dialog"
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table"

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
  remarks: string | null
  module_mapping_count: number
}

interface AssetFormData {
  name: string
  asset_type: string
  description: string
  remarks: string
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
  const [errorDialog, setErrorDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })
  const [warningDialog, setWarningDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [viewMode, setViewMode] = useState<"cards" | "list">("cards")
  const [sorting, setSorting] = useState<SortingState>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<AssetFormData>({
    name: "",
    asset_type: "information_asset",
    description: "",
    remarks: "",
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
  const [showModuleDialog, setShowModuleDialog] = useState(false)
  const [selectedAssetForModule, setSelectedAssetForModule] = useState<AssetListItem | null>(null)
  const [moduleSearch, setModuleSearch] = useState("")
  const [availableModules, setAvailableModules] = useState<{id: string; code: string; name: string; module_group: string}[]>([])
  const [loadingModules, setLoadingModules] = useState(false)
  const [moduleJustification, setModuleJustification] = useState("")
  const [assigningModule, setAssigningModule] = useState(false)
  const [showAddProcess, setShowAddProcess] = useState(false)
  const [selectedProcess, setSelectedProcess] = useState<string | null>(null)
  const [loadingProcesses, setLoadingProcesses] = useState(false)
  const [unlinkedProcesses, setUnlinkedProcesses] = useState<BusinessProcessOption[]>([])
  const [newLinkedProcessIds, setNewLinkedProcessIds] = useState<string[]>([])
  const [allProcesses, setAllProcesses] = useState<BusinessProcessOption[]>([])
  const [processesExpanded, setProcessesExpanded] = useState(false)
  const [processSearch, setProcessSearch] = useState("")
  
  // Edit dialog module state
  const [editModuleSearch, setEditModuleSearch] = useState("")
  const [editAvailableModules, setEditAvailableModules] = useState<{id: string; code: string; name: string; module_group: string}[]>([])
  const [editLoadingModules, setEditLoadingModules] = useState(false)
  const [editModuleJustification, setEditModuleJustification] = useState("")
  const [assetModules, setAssetModules] = useState<{id: string; module_id: string; module_code: string; module_name: string; module_group: string; justification: string | null}[]>([])
  const [loadingAssetModules, setLoadingAssetModules] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{
    total: number
    created: number
    updated: number
    skipped_scoped: number
    duplicate_file: boolean
    file_storage_path: string
    errors: { row: number; message: string }[]
  } | null>(null)
  const [showImportResult, setShowImportResult] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const table = useReactTable({
    data: assets,
    columns: useMemo(() => [
      {
        accessorKey: "name",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("common.name")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => <span className="font-medium">{row.getValue("name")}</span>,
      },
      {
        accessorKey: "asset_type",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.type")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => (
          <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200">
            {t(`assets.types.${row.getValue("asset_type")}`) || row.getValue("asset_type")}
          </Badge>
        ),
      },
      {
        accessorKey: "lifecycle_status",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("common.status")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const status = row.getValue("lifecycle_status") as string
          return (
            <Badge variant="outline" className={statusColors[status] || statusColors.inactive}>
              {t(`assets.statusLevels.${status}`) || status}
            </Badge>
          )
        },
      },
      {
        accessorKey: "criticality",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.criticality")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const crit = row.getValue("criticality") as string
          return (
            <Badge variant="outline" className={criticalityColors[crit] || criticalityColors.normal}>
              {t(`assets.criticalityLevels.${crit}`) || crit}
            </Badge>
          )
        },
      },
      {
        id: "protection",
        accessorFn: (row: any) => `${row.confidentiality_need}${row.integrity_need}${row.availability_need}`,
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.protection")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const asset = row.original
          return (
            <div className="flex gap-1">
              <Badge variant="outline" className={`${protectionNeedColors[asset.confidentiality_need]} text-xs`}>
                C:{t(`protectionNeed.${asset.confidentiality_need}`)?.charAt(0) || asset.confidentiality_need?.charAt(0)}
              </Badge>
              <Badge variant="outline" className={`${protectionNeedColors[asset.integrity_need]} text-xs`}>
                I:{t(`protectionNeed.${asset.integrity_need}`)?.charAt(0) || asset.integrity_need?.charAt(0)}
              </Badge>
              <Badge variant="outline" className={`${protectionNeedColors[asset.availability_need]} text-xs`}>
                A:{t(`protectionNeed.${asset.availability_need}`)?.charAt(0) || asset.availability_need?.charAt(0)}
              </Badge>
            </div>
          )
        },
      },
      {
        id: "owner",
        accessorFn: (row: any) => row.owner?.name || "",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.owner")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const owner = row.original.owner as OwnerInfo | null
          return owner?.name || "-"
        },
      },
      {
        accessorKey: "linked_process_count",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.linkedProcesses")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const count = row.getValue("linked_process_count") as number
          return (
            <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 dark:text-blue-200">
              {count}
            </Badge>
          )
        },
      },
      {
        accessorKey: "module_mapping_count",
        header: ({ column }: any) => (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-4 h-8"
          >
            {t("assets.modules")}
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        ),
        cell: ({ row }: any) => {
          const count = row.original.module_mapping_count as number
          return count > 0 ? (
            <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900 dark:text-purple-200 cursor-pointer" onClick={(e) => { e.stopPropagation(); const asset = row.original; setSelectedAssetForModule(asset); setShowModuleDialog(true); setModuleSearch(""); setModuleJustification(""); setAvailableModules([]); }}>
              {count}
            </Badge>
          ) : (
            <span className="text-muted-foreground text-sm">-</span>
          )
        },
      },
      {
        id: "actions",
        header: t("common.actions"),
        cell: ({ row }: any) => {
          const asset = row.original
          return (
            <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm" onClick={() => { console.log("Assign module click", asset.id, asset.name); setSelectedAssetForModule(asset); setShowModuleDialog(true); setModuleSearch(""); setModuleJustification(""); setAvailableModules([]); }}>
                <BookOpen className="h-4 w-4 mr-1" />
                {t("assets.assignModule")}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => confirmDelete(asset.id)} className="text-destructive hover:text-destructive">
                {t("common.delete")}
              </Button>
            </div>
          )
        },
      },
    ], [t]),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: { sorting },
    onSortingChange: setSorting,
  })

  useEffect(() => { selectedOrgIdRef.current = selectedOrgId }, [selectedOrgId])

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!selectedOrgIdRef.current || !token) return
    fetchUsers()
    fetchPersons()
    fetchAllProcesses()
    fetchAssets()
  }, [selectedOrgId, typeFilter, statusFilter, search, sorting])

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

  const fetchAllProcesses = async () => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      const response = await apiClient.get("/business-processes/")
      const processes = response.data?.results || response.data || []
      setAllProcesses(Array.isArray(processes) ? processes : [])
    } catch (err) {
      console.error("Failed to fetch processes:", err)
      setAllProcesses([])
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
      if (sorting.length > 0) {
        params.sort = sorting[0].id
        params.dir = sorting[0].desc ? "desc" : "asc"
      }
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
      remarks: "",
      criticality: "normal",
      confidentiality_need: "normal",
      integrity_need: "normal",
      availability_need: "normal",
      lifecycle_status: "active",
      owner_user_id: null,
      person_id: null,
    })
    setNewLinkedProcessIds([])
    setProcessSearch("")
    setProcessesExpanded(false)
    setShowForm(true)
  }

  const handleEdit = (asset: AssetListItem) => {
    setEditingId(asset.id)
    setProcessSearch("")
    setProcessesExpanded(false)
    setFormData({
      name: asset.name,
      asset_type: asset.asset_type,
      description: "",
      remarks: asset.remarks || "",
      criticality: asset.criticality,
      confidentiality_need: asset.confidentiality_need,
      integrity_need: asset.integrity_need,
      availability_need: asset.availability_need,
      lifecycle_status: asset.lifecycle_status,
      owner_user_id: asset.owner_user_id,
      person_id: asset.person_id,
    })
    resetEditModuleState()
    fetchAssetModules(asset.id)
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
        const createResponse = await apiClient.post("/assets/", payload)
        const newAssetId = createResponse.data?.id
        if (newAssetId && newLinkedProcessIds.length > 0) {
          for (const processId of newLinkedProcessIds) {
            await apiClient.post(`/assets/${newAssetId}/link-process/`, { process_id: processId })
          }
        }
      }
      setShowForm(false)
      fetchAssets()
    } catch (err: any) {
      console.error("DEBUG handleSubmit error:", err.response?.data || err)
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to save" })
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

  const searchModules = async (query: string) => {
    console.log("searchModules called with:", query)
    if (query.length < 2) {
      setAvailableModules([])
      return
    }
    setLoadingModules(true)
    try {
      const response = await apiClient.get("/catalog/modules", { params: { search: query } })
      console.log("Modules response:", response.data?.length, "modules")
      setAvailableModules(response.data?.slice(0, 20) || [])
    } catch (err) {
      console.error("Failed to search modules:", err)
      setAvailableModules([])
    } finally {
      setLoadingModules(false)
    }
  }

  const searchModulesForEdit = async (query: string) => {
    if (query.length < 2) {
      setEditAvailableModules([])
      return
    }
    setEditLoadingModules(true)
    try {
      const response = await apiClient.get("/catalog/modules", { params: { search: query } })
      setEditAvailableModules(response.data?.slice(0, 20) || [])
    } catch (err) {
      console.error("Failed to search modules:", err)
      setEditAvailableModules([])
    } finally {
      setEditLoadingModules(false)
    }
  }

  const fetchAssetModules = async (assetId: string) => {
    setLoadingAssetModules(true)
    try {
      const response = await apiClient.get("/asset-module-mappings/", { params: { asset_id: assetId } })
      const transformed = (response.data || []).map((m: any) => ({
        id: m.id,
        module_id: m.module_id,
        module_code: m.module?.code || "",
        module_name: m.module?.name || "",
        module_group: m.module?.module_group || "",
        justification: m.justification,
      }))
      setAssetModules(transformed)
    } catch (err) {
      console.error("Failed to fetch asset modules:", err)
      setAssetModules([])
    } finally {
      setLoadingAssetModules(false)
    }
  }

  const handleAssignModuleInEdit = async (moduleId: string) => {
    if (!editingId) return
    setAssigningModule(true)
    try {
      await apiClient.post("/asset-module-mappings/", {
        asset_id: editingId,
        module_id: moduleId,
        justification: editModuleJustification || null,
      })
      await apiClient.post("/asset-module-mappings/generate-imr", null, {
        params: { asset_id: editingId },
      })
      setEditModuleSearch("")
      setEditModuleJustification("")
      setEditAvailableModules([])
      fetchAssetModules(editingId)
      fetchAssets()
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Unknown error"
      setErrorDialog({ open: true, message: t("assets.moduleAssignError", { error: errorMsg }) })
    } finally {
      setAssigningModule(false)
    }
  }

  const handleRemoveModule = async (mappingId: string) => {
    if (!confirm(t("targets.confirmRemoveModule"))) return
    try {
      await apiClient.delete(`/asset-module-mappings/${mappingId}`)
      if (editingId) fetchAssetModules(editingId)
      fetchAssets()
    } catch (err: any) {
      console.error("Failed to remove module:", err)
    }
  }

  const resetEditModuleState = () => {
    setEditModuleSearch("")
    setEditModuleJustification("")
    setEditAvailableModules([])
    setAssetModules([])
  }

  const handleAssignModule = async (moduleId: string) => {
    if (!selectedAssetForModule || !selectedOrgIdRef.current) return
    setAssigningModule(true)
    try {
      await apiClient.post("/asset-module-mappings/", {
        asset_id: selectedAssetForModule.id,
        module_id: moduleId,
        justification: moduleJustification || null,
      })
      await apiClient.post("/asset-module-mappings/generate-imr", null, {
        params: { asset_id: selectedAssetForModule.id },
      })
      setShowModuleDialog(false)
      setWarningDialog({ open: true, message: t("assets.moduleAssignedSuccess", { code: "?", count: 0 }) })
      fetchAssets()
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Unknown error"
      setErrorDialog({ open: true, message: t("assets.moduleAssignError", { error: errorMsg }) })
    } finally {
      setAssigningModule(false)
    }
  }

  const fetchUnlinkedProcesses = async (assetId: string) => {
    if (!selectedOrgIdRef.current) return
    const token = localStorage.getItem("access_token")
    if (!token) return
    try {
      setLoadingProcesses(true)
      console.log("Fetching unlinked processes for asset:", assetId)
      const response = await apiClient.get(`/assets/${assetId}/unlinked-processes`)
      console.log("Unlinked processes response:", response.data)
      setUnlinkedProcesses(response.data || [])
      setSelectedProcess("")
    } catch (err: any) {
      console.error("Failed to fetch unlinked processes:", err.response?.data || err)
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
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to link process" })
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
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to unlink process" })
    }
  }

  const toggleProcess = (processId: string) => {
    if (newLinkedProcessIds.includes(processId)) {
      setNewLinkedProcessIds(newLinkedProcessIds.filter(id => id !== processId))
    } else {
      setNewLinkedProcessIds([...newLinkedProcessIds, processId])
    }
  }

  const toggleAllProcesses = (select: boolean) => {
    if (select) {
      setNewLinkedProcessIds(filteredProcesses.map(p => p.id))
    } else {
      setNewLinkedProcessIds([])
    }
  }

  const filteredProcesses = allProcesses.filter(p => 
    p.name.toLowerCase().includes(processSearch.toLowerCase())
  )

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

  const handleImportCsv = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImporting(true)
    setImportResult(null)
    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("on_conflict", "update")

      const response = await apiClient.post("/assets/import-csv", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      setImportResult(response.data)
    } catch (err: any) {
      setImportResult({
        total: 0, created: 0, updated: 0, skipped_scoped: 0,
        duplicate_file: false, file_storage_path: "",
        errors: [{ row: 0, message: err.response?.data?.detail || err.message || "Import failed" }],
      })
    } finally {
      setShowImportResult(true)
      setImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
      fetchAssets()
    }
  }

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
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleImportCsv}
            className="hidden"
          />
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
          >
            {importing ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />{t("common.loading")}</>
            ) : (
              <><Upload className="h-4 w-4 mr-2" />{t("assets.importCsv")}</>
            )}
          </Button>
          <Button onClick={handleCreate}>{t("common.add")}</Button>
        </div>
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
          <option value="">{t("common.allTypes")}</option>
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
          <option value="">{t("common.allStatuses")}</option>
          {statusLevels.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === "cards" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("cards")}
            className="rounded-r-none"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("list")}
            className="rounded-l-none"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {filteredAssets.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{t("assets.noData")}</p>
          </CardContent>
        </Card>
      )}

      {filteredAssets.length > 0 && viewMode === "cards" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAssets.map((asset) => (
            <Card key={asset.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleEdit(asset)}>
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
                               {asset.can_manage_links && (
                               <Button
                                 variant="ghost"
                                 size="sm"
                                 onClick={() => handleUnlinkProcess(asset.id, proc.id)}
                                 className="text-destructive hover:text-destructive h-6 px-1"
                               >
                                 <Unlink className="h-3 w-3" />
                               </Button>
                               )}
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
                <div className="flex items-center gap-2 mt-4" onClick={(e) => e.stopPropagation()}>
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

      {filteredAssets.length > 0 && viewMode === "list" && (
        <div className="border rounded-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="px-4 py-3 text-left text-sm font-medium">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr 
                  key={row.id} 
                  className="border-t hover:bg-muted/50 cursor-pointer"
                  onClick={() => handleEdit(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
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
                  placeholder={t("assets.namePlaceholder")}
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
                  placeholder={t("assets.descPlaceholder")}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">{t("assets.remarks")}</label>
                <textarea
                  value={formData.remarks}
                  onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                  placeholder={t("assets.remarksPlaceholder") || "Additional notes, comments..."}
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

              <div className="border rounded-md mt-4">
                <button
                  type="button"
                  onClick={() => setProcessesExpanded(!processesExpanded)}
                  className="flex items-center justify-between w-full p-3 bg-muted hover:bg-muted/80 transition-colors rounded-t-md"
                >
                  <span className="flex items-center gap-2">
                    <Link2 className="h-4 w-4" />
                    <span className="text-sm font-medium">{t("assets.linkedProcessesSection")}</span>
                    {(editingId ? (getEditingAsset()?.linked_processes?.length || 0) : newLinkedProcessIds.length) > 0 && (
                      <Badge variant="default" className="text-xs">
                        {editingId ? (getEditingAsset()?.linked_processes?.length || 0) : newLinkedProcessIds.length}
                      </Badge>
                    )}
                  </span>
                  <ChevronDown className={`h-4 w-4 transition-transform ${processesExpanded ? "rotate-180" : ""} ${editingId ? "hidden" : ""}`} />
                </button>
                
                {processesExpanded && (
                  <div className="p-3 space-y-3">
                    {!editingId ? (
                      <>
                        <Input
                          placeholder={t("assets.searchProcesses") || "Search processes..."}
                          value={processSearch}
                          onChange={(e) => setProcessSearch(e.target.value)}
                          className="h-9"
                        />
                        
                        {filteredProcesses.length > 0 ? (
                          <>
                            <label className="flex items-center gap-2 cursor-pointer text-sm">
                              <input
                                type="checkbox"
                                checked={filteredProcesses.length > 0 && newLinkedProcessIds.length === filteredProcesses.length}
                                onChange={(e) => toggleAllProcesses(e.target.checked)}
                                className="rounded border-input"
                              />
                              <span className="text-muted-foreground">
                                {newLinkedProcessIds.length === 0 ? t("common.selectAll") : t("common.selectNone")}
                              </span>
                            </label>
                            
                            <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                              {filteredProcesses.map((proc) => (
                                <div
                                  key={proc.id}
                                  onClick={() => toggleProcess(proc.id)}
                                  className={`p-3 border rounded cursor-pointer transition-all ${
                                    newLinkedProcessIds.includes(proc.id) 
                                      ? "border-primary bg-primary/10 ring-1 ring-primary" 
                                      : "hover:bg-secondary border-border"
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <input
                                        type="checkbox"
                                        checked={newLinkedProcessIds.includes(proc.id)}
                                        onChange={() => toggleProcess(proc.id)}
                                        className="rounded border-input pointer-events-none"
                                      />
                                      <span className="font-medium">{proc.name}</span>
                                    </div>
                                    <Badge variant="outline" className={`${statusColors[proc.status]} text-xs`}>
                                      {t(`common.${proc.status}`) || proc.status}
                                    </Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </>
                        ) : (
                          <p className="text-sm text-muted text-center py-4">{t("common.noData")}</p>
                        )}
                      </>
                    ) : getEditingAsset() && (
                      <>
                        {getEditingAsset()!.linked_processes && getEditingAsset()!.linked_processes.length > 0 ? (
                          <div className="space-y-2">
                            {getEditingAsset()!.linked_processes.map((proc) => (
                              <div key={proc.id} className="flex items-center justify-between p-3 border rounded bg-secondary">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{proc.name}</span>
                                  <Badge variant="outline" className={`${statusColors[proc.status]} text-xs`}>
                                    {t(`common.${proc.status}`) || proc.status}
                                  </Badge>
                                </div>
                                {getEditingAsset()!.can_manage_links && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleUnlinkProcess(editingId, proc.id)}
                                    className="text-destructive hover:text-destructive h-7"
                                  >
                                    <Unlink className="h-4 w-4 mr-1" />
                                    {t("assets.unlink")}
                                  </Button>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground text-center py-4">{t("assets.noLinkedProcesses")}</p>
                        )}

                        {getEditingAsset()!.can_manage_links && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openAddProcess(editingId)}
                            className="w-full"
                          >
                            <Link2 className="h-4 w-4 mr-1" />
                            {t("assets.addToProcess")}
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Module Section in Edit Dialog */}
              <div className="border rounded-lg p-4 mt-4">
                <h4 className="text-sm font-medium mb-3">{t("targets.mappedModules")}</h4>
                {loadingAssetModules ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {t("common.loading")}
                  </div>
                ) : assetModules.length > 0 ? (
                  <div className="space-y-2">
                    {assetModules.map((mod) => (
                      <div
                        key={mod.id}
                        className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <code className="text-sm font-mono">{mod.module_code}</code>
                            <span className="text-sm">{mod.module_name}</span>
                            <Badge variant="outline" className="text-xs">{mod.module_group}</Badge>
                          </div>
                          {mod.justification && (
                            <p className="text-xs text-muted-foreground mt-1">{mod.justification}</p>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-700"
                          onClick={() => handleRemoveModule(mod.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">{t("targets.noModules")}</p>
                )}

                {/* Add Module in Edit */}
                <div className="mt-4 pt-4 border-t">
                  <Label className="text-sm">{t("targets.addModule")}</Label>
                  <Input
                    className="mt-2"
                    value={editModuleSearch}
                    onChange={(e) => {
                      setEditModuleSearch(e.target.value)
                      searchModulesForEdit(e.target.value)
                    }}
                    placeholder={t("assets.searchModule")}
                  />
                  <textarea
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-2"
                    value={editModuleJustification}
                    onChange={(e) => setEditModuleJustification(e.target.value)}
                    placeholder={t("assets.justification")}
                  />
                  {editLoadingModules ? (
                    <div className="flex items-center gap-2 text-muted-foreground mt-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t("common.loading")}
                    </div>
                  ) : editAvailableModules.length > 0 ? (
                    <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                      {editAvailableModules.map((mod) => (
                        <div
                          key={mod.id}
                          className="flex items-center justify-between p-2 bg-muted/30 rounded hover:bg-muted/50 cursor-pointer"
                          onClick={() => handleAssignModuleInEdit(mod.id)}
                        >
                          <div className="flex items-center gap-2">
                            <code className="text-sm font-mono">{mod.code}</code>
                            <span className="text-sm">{mod.name}</span>
                          </div>
                          <Badge variant="outline" className="text-xs">{mod.module_group}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : editModuleSearch.length >= 2 ? (
                    <p className="text-sm text-muted-foreground mt-2">{t("assets.noModulesFound")}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground mt-2">{t("targets.typeToSearch")}</p>
                  )}
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

      {/* Module Assignment Dialog */}
      <Dialog open={showModuleDialog} onOpenChange={setShowModuleDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("assets.moduleAssignmentTitle")}</DialogTitle>
            <DialogDescription>{t("assets.moduleAssignmentDesc")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedAssetForModule && selectedAssetForModule.linked_process_count === 0 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-800 text-sm">
                {t("assets.noBPWarning")}
              </div>
            )}
            <div>
              <Label>{t("assets.searchModule")}</Label>
              <Input
                value={moduleSearch}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setModuleSearch(e.target.value)
                  searchModules(e.target.value)
                }}
                placeholder={t("assets.searchModule")}
              />
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {loadingModules ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t("common.loading")}
                </div>
              ) : availableModules.length > 0 ? (
                availableModules.map((mod) => (
                  <div
                    key={mod.id}
                    className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 cursor-pointer"
                    onClick={() => handleAssignModule(mod.id)}
                  >
                    <div>
                      <code className="text-sm font-mono">{mod.code}</code>
                      <span className="text-sm ml-2">{mod.name}</span>
                    </div>
                    <Badge variant="outline">{mod.module_group}</Badge>
                  </div>
                ))
              ) : moduleSearch.length >= 2 ? (
                <p className="text-sm text-muted-foreground">{t("assets.noModulesFound")}</p>
              ) : (
                <p className="text-sm text-muted-foreground">{t("assets.searchHint")}</p>
              )}
            </div>
            <div>
              <Label>{t("assets.justification")}</Label>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={moduleJustification}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setModuleJustification(e.target.value)}
                placeholder={t("assets.justification")}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModuleDialog(false)} disabled={assigningModule}>
              {t("common.cancel")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import CSV Result Dialog */}
      <Dialog open={showImportResult} onOpenChange={setShowImportResult}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("assets.importResult")}</DialogTitle>
            <DialogDescription>
              {t("assets.importResultDesc")}
            </DialogDescription>
          </DialogHeader>
          {importResult && (
            <div className="space-y-3">
              {importResult.duplicate_file ? (
                <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800">
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    {t("assets.importDuplicate")}
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-2xl font-bold">{importResult.total}</p>
                      <p className="text-xs text-muted-foreground">{t("assets.importTotal")}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950 text-center">
                      <p className="text-2xl font-bold text-green-700 dark:text-green-300">{importResult.created}</p>
                      <p className="text-xs text-green-600 dark:text-green-400">{t("assets.importCreated")}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950 text-center">
                      <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{importResult.updated}</p>
                      <p className="text-xs text-blue-600 dark:text-blue-400">{t("assets.importUpdated")}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950 text-center">
                      <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">{importResult.skipped_scoped}</p>
                      <p className="text-xs text-yellow-600 dark:text-yellow-400">{t("assets.importSkipped")}</p>
                    </div>
                  </div>
                  {importResult.errors.length > 0 && (
                    <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800">
                      <p className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">{t("assets.importErrors")}</p>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {importResult.errors.map((err, i) => (
                          <p key={i} className="text-xs text-red-700 dark:text-red-300">
                            Rida {err.row}: {err.message}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowImportResult(false)}>
              OK
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ErrorDialog
        open={errorDialog.open}
        onOpenChange={(open) => setErrorDialog(prev => ({ ...prev, open }))}
        title="Error"
        message={errorDialog.message}
      />

      <WarningDialog
        open={warningDialog.open}
        onOpenChange={(open) => setWarningDialog(prev => ({ ...prev, open }))}
        title="Warning"
        message={warningDialog.message}
      />
    </div>
  )
}
    

      