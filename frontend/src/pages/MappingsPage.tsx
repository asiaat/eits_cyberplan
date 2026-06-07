import { useState, useEffect, useRef, useMemo } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Link2, Unlink, AlertTriangle, Shield, CheckCircle2, XCircle, CheckSquare, Loader2, GitBranch } from "lucide-react"
import { ErrorDialog } from "@/components/ui/error-dialog"
import { WarningDialog } from "@/components/ui/warning-dialog"
import { Tree } from "react-arborist"
import type { NodeRendererProps } from "react-arborist"

interface TreeNode {
  assetId: string
  assetName: string
  assetType: string
  children?: TreeNode[]
  relationType?: string
  relationTypeName?: string
  direction: "upstream" | "downstream"
  relationId?: string
}

interface LinkedProcess {
  id: string
  name: string
  status: string
}

interface Person {
  id: string
  name: string
}

interface AssetItem {
  id: string
  name: string
  asset_type: string
  person_id?: string | null
  linked_processes?: LinkedProcess[]
}

interface BpItem {
  id: string
  name: string
  confidentiality_need: string
  integrity_need: string
  availability_need: string
}

interface ModuleItem {
  id: string
  code: string
  name: string
  module_group: string | null
}

interface AssetMappingItem {
  id: string
  asset_id: string
  module_id: string
  module: { code: string; name: string; module_group: string | null } | null
  modeled_at: string | null
}

interface BpMappingItem {
  id: string
  business_process_id: string
  business_process_name: string
  module_id: string
  module_code: string
  module_name: string
  module_group: string | null
  modeled_at: string | null
}

interface ProtectionModeItem {
  id: string
  security_approach: string
  is_active: boolean
}

interface ProtectionNeedItem {
  id: string
  business_process_id: string
  protection_need: string
  approved_by: string | null
}

const ASSET_TYPES = ["all", "information_asset", "software", "hardware", "service", "data", "competence", "other"] as const

const MODULE_GROUPS = ["ISMS", "ORP", "CON", "OPS", "DER", "INF", "NET", "SYS", "APP", "IND"] as const

const approachColorMap: Record<string, string> = {
  BASIC: "bg-green-100 text-green-800 border-green-200",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200",
  CORE: "bg-red-100 text-red-800 border-red-200",
}

const ciaColorMap: Record<string, string> = {
  normal: "bg-green-100 text-green-700 border-green-200",
  high: "bg-yellow-100 text-yellow-700 border-yellow-200",
  very_high: "bg-red-100 text-red-700 border-red-200",
  unknown: "bg-gray-100 text-gray-500 border-gray-200",
}

export default function MappingsPage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const orgRef = useRef(selectedOrgId)

  const [assets, setAssets] = useState<AssetItem[]>([])
  const [bps, setBps] = useState<BpItem[]>([])
  const [modules, setModules] = useState<ModuleItem[]>([])
  const [assetMappings, setAssetMappings] = useState<AssetMappingItem[]>([])
  const [bpMappings, setBpMappings] = useState<BpMappingItem[]>([])
  const [protectionMode, setProtectionMode] = useState<ProtectionModeItem | null>(null)
  const [protectionNeeds, setProtectionNeeds] = useState<ProtectionNeedItem[]>([])
  const [persons, setPersons] = useState<Person[]>([])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errorDialog, setErrorDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })
  const [warningDialog, setWarningDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })
  const [mainTab, setMainTab] = useState("assets")
  const [assetTypeTab, setAssetTypeTab] = useState("all")
  const [moduleGroupTab, setModuleGroupTab] = useState("ISMS")
  const [selectedAssetIds, setSelectedAssetIds] = useState<Set<string>>(new Set())
  const [selectedModuleIds, setSelectedModuleIds] = useState<Set<string>>(new Set())
  const [scopeTab, setScopeTab] = useState<"select" | "mapped">("select")
  const [moduleSort, setModuleSort] = useState<"code" | "name">("code")
  const [moduleGroupFilter, setModuleGroupFilter] = useState("all")
  const [batchResult, setBatchResult] = useState<string | null>(null)

  const [editingBp, setEditingBp] = useState<BpItem | null>(null)
  const [editForm, setEditForm] = useState({ confidentiality: "", integrity: "", availability: "" })
  const [bpTargetId, setBpTargetId] = useState("")
  const [bpModuleId, setBpModuleId] = useState("")

  // Asset Relations state
  const [assetRelations, setAssetRelations] = useState<any[]>([])
  const [loadingRelations, setLoadingRelations] = useState(false)
  const [relationTypes, setRelationTypes] = useState<any[]>([])
  const [selectedSourceAssetIds, setSelectedSourceAssetIds] = useState<Set<string>>(new Set())
  const [selectedTargetAssetIds, setSelectedTargetAssetIds] = useState<Set<string>>(new Set())
  const [sourceAssetTypeTab, setSourceAssetTypeTab] = useState("all")
  const [targetAssetTypeTab, setTargetAssetTypeTab] = useState("all")
  const [selectedRelationTypeCode, setSelectedRelationTypeCode] = useState("")
  const [relationDirectionFilter] = useState<"all" | "upstream" | "downstream">("all")
  const [createRelationResult, setCreateRelationResult] = useState<string | null>(null)
  const [customRelationText, setCustomRelationText] = useState("")
  const [relationViewMode, setRelationViewMode] = useState<"list" | "tree">("list")
  const [relationTreeDirection, setRelationTreeDirection] = useState<"depends_on" | "required_by" | "all">("depends_on")

  useEffect(() => { orgRef.current = selectedOrgId }, [selectedOrgId])

  const activeMode = protectionMode?.is_active ? protectionMode : null

  const fetchData = async () => {
    if (!selectedOrgId) return
    setLoading(true)
    try {
      const [assetsRes, bpsRes, modulesRes, assetMapRes, bpMapRes, modeRes, pnRes, personsRes] = await Promise.all([
        apiClient.get("/assets/"),
        apiClient.get("/business-processes/"),
        apiClient.get("/catalog/modules"),
        apiClient.get("/asset-module-mappings/"),
        apiClient.get("/modeling/bp-mappings"),
        apiClient.get("/protection-mode/"),
        apiClient.get("/eits/protection-needs"),
        apiClient.get("/persons/"),
      ])
      setAssets(assetsRes.data || [])
      setBps(bpsRes.data || [])
      setModules(modulesRes.data || [])
      setAssetMappings(assetMapRes.data || [])
      setBpMappings(bpMapRes.data || [])
      setProtectionNeeds(pnRes.data || [])
      setPersons(personsRes.data || [])
      const active = (modeRes.data || []).find((m: ProtectionModeItem) => m.is_active)
      setProtectionMode(active || null)
    } catch {
      setErrorDialog({ open: true, message: "Failed to load data" })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [selectedOrgId])

  useEffect(() => {
    if (mainTab === "asset_relations") {
      fetchRelationTypes()
      fetchAllAssetRelations()
    }
  }, [mainTab, selectedOrgId])

  const filteredAssets = assets.filter(a =>
    a.asset_type === assetTypeTab || assetTypeTab === "all"
  ).filter(a => a.linked_processes && a.linked_processes.length > 0)

  const selectedAssetMappings = useMemo(() => {
    return assetMappings.filter(m => selectedAssetIds.has(m.asset_id))
  }, [assetMappings, selectedAssetIds])

  const mappingsByGroup = useMemo(() => {
    const map: Record<string, AssetMappingItem[]> = {}
    for (const m of selectedAssetMappings) {
      const group = m.module?.module_group || "OTHER"
      if (!map[group]) map[group] = []
      map[group].push(m)
    }
    return map
  }, [selectedAssetMappings])

  const availableGroups = useMemo(() => {
    return MODULE_GROUPS.filter(g => mappingsByGroup[g]?.length)
  }, [mappingsByGroup])

  const activeModuleGroup = availableGroups.includes(moduleGroupTab as any)
    ? moduleGroupTab
    : (availableGroups[0] || "ISMS")

  const typeCounts = useMemo(() => {
    const filteredForBp = assets.filter(a => a.linked_processes && a.linked_processes.length > 0)
    const counts: Record<string, number> = { all: filteredForBp.length }
    for (const t of ASSET_TYPES) {
      if (t !== "all") counts[t] = filteredForBp.filter(a => a.asset_type === t).length
    }
    return counts
  }, [assets])

  const filteredSourceAssets = useMemo(() => {
    return assets.filter(a => sourceAssetTypeTab === "all" || a.asset_type === sourceAssetTypeTab)
  }, [assets, sourceAssetTypeTab])

  const filteredTargetAssets = useMemo(() => {
    return assets.filter(a => targetAssetTypeTab === "all" || a.asset_type === targetAssetTypeTab)
  }, [assets, targetAssetTypeTab])

  const sourceTypeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: filteredSourceAssets.length }
    for (const t of ASSET_TYPES) {
      if (t !== "all") counts[t] = filteredSourceAssets.filter(a => a.asset_type === t).length
    }
    return counts
  }, [filteredSourceAssets])

  const targetTypeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: filteredTargetAssets.length }
    for (const t of ASSET_TYPES) {
      if (t !== "all") counts[t] = filteredTargetAssets.filter(a => a.asset_type === t).length
    }
    return counts
  }, [filteredTargetAssets])

  const filteredRelations = useMemo(() => {
    if (relationDirectionFilter === "all") return assetRelations
    return assetRelations.filter(r => r.direction === relationDirectionFilter)
  }, [assetRelations, relationDirectionFilter])

  const sortedModules = useMemo(() => {
    const sorted = [...modules]
    sorted.sort((a, b) => {
      if (moduleSort === "code") return a.code.localeCompare(b.code)
      return a.name.localeCompare(b.name)
    })
    return sorted
  }, [modules, moduleSort])

  const filteredModules = useMemo(() => {
    let result = sortedModules
    if (moduleGroupFilter !== "all") {
      result = result.filter(m => m.module_group === moduleGroupFilter)
    }
    if (selectedAssetIds.size > 0) {
      const mapped = new Set(selectedAssetMappings.map(m => m.module_id))
      result = result.filter(m => !mapped.has(m.id))
    }
    return result
  }, [sortedModules, moduleGroupFilter, selectedAssetIds, selectedAssetMappings])

  const moduleGroupCounts = useMemo(() => {
    const mapped = selectedAssetIds.size > 0
      ? new Set(selectedAssetMappings.map(m => m.module_id))
      : new Set<string>()
    const counts: Record<string, number> = { all: modules.filter(m => !mapped.has(m.id)).length }
    for (const g of MODULE_GROUPS) {
      counts[g] = modules.filter(m => m.module_group === g && !mapped.has(m.id)).length
    }
    return counts
  }, [modules, selectedAssetIds, selectedAssetMappings])

  const personMap = useMemo(() => {
  const map: Record<string, string> = {}
  for (const p of persons) map[p.id] = p.name
  return map
}, [persons])

const approvedBpIds = new Set([
    ...protectionNeeds.filter((pn) => pn.approved_by).map((pn) => pn.business_process_id),
    ...bps.filter((bp: any) =>
      bp.confidentiality_need !== null && bp.confidentiality_need !== "" && bp.confidentiality_need !== "unknown" ||
      bp.integrity_need !== null && bp.integrity_need !== "" && bp.integrity_need !== "unknown" ||
      bp.availability_need !== null && bp.availability_need !== "" && bp.availability_need !== "unknown"
    ).map((bp: any) => bp.id)
  ])

  const handleSelectAll = () => {
    if (selectedAssetIds.size === filteredAssets.length && filteredAssets.length > 0) {
      setSelectedAssetIds(new Set())
    } else {
      setSelectedAssetIds(new Set(filteredAssets.map(a => a.id)))
    }
  }

  const handleToggleAsset = (id: string) => {
    const next = new Set(selectedAssetIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedAssetIds(next)
  }

  const handleBatchMap = async () => {
    if (selectedAssetIds.size === 0 || selectedModuleIds.size === 0) {
      setBatchResult("Select assets and at least one module")
      return
    }
    setSaving(true)
    setBatchResult(null)
    try {
      const res = await apiClient.post("/modeling/batch-map", {
        module_ids: Array.from(selectedModuleIds),
        target_ids: Array.from(selectedAssetIds),
        target_type: "asset",
      })
      const data = res.data
      const mapped = data.mapped?.length || 0
      const skipped = data.skipped?.length || 0
      const errors = data.errors?.length || 0
      setBatchResult(`Mapped: ${mapped}, Skipped: ${skipped}, Errors: ${errors}`)
      setSelectedModuleIds(new Set())
      await fetchData()
    } catch (err: any) {
      setBatchResult(err.response?.data?.detail || "Batch mapping failed")
    } finally {
      setSaving(false)
    }
  }

  const handleMapModuleToBp = async () => {
    if (!bpTargetId || !bpModuleId) {
      setWarningDialog({ open: true, message: "Select both a BP and a module" })
      return
    }
    setSaving(true)
    try {
      await apiClient.post("/modeling/map", null, {
        params: { module_id: bpModuleId, target_type: "business_process", target_id: bpTargetId },
      })
      setBpTargetId("")
      setBpModuleId("")
      await fetchData()
    } catch (err: any) {
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to map module" })
    } finally {
      setSaving(false)
    }
  }

  const handleRemoveAssetMapping = async (id: string) => {
    if (!confirm("Remove this module from scope?")) return
    try {
      await apiClient.delete(`/modeling/map/${id}`, { params: { target_type: "asset" } })
      await fetchData()
    } catch (err: any) {
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to remove mapping" })
    }
  }

  const handleRemoveBpMapping = async (id: string) => {
    if (!confirm("Remove this module from scope?")) return
    try {
      await apiClient.delete(`/modeling/map/${id}`, { params: { target_type: "business_process" } })
      await fetchData()
    } catch (err: any) {
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to remove mapping" })
    }
  }

  const handleEditProtectionNeed = (bp: BpItem) => {
    if (activeMode) {
      setWarningDialog({ open: true, message: t("mappings.modeLocked") })
      return
    }
    setEditingBp(bp)
    setEditForm({
      confidentiality: bp.confidentiality_need,
      integrity: bp.integrity_need,
      availability: bp.availability_need,
    })
  }

  const handleSaveProtectionNeed = async () => {
    if (!editingBp) return
    setSaving(true)
    try {
      await apiClient.patch(`/modeling/business-process/${editingBp.id}/protection-need`, null, {
        params: {
          confidentiality: editForm.confidentiality,
          integrity: editForm.integrity,
          availability: editForm.availability,
        },
      })
      setEditingBp(null)
      await fetchData()
    } catch (err: any) {
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to update protection needs" })
    } finally {
      setSaving(false)
    }
  }

  const getAssetName = (assetId: string) => assets.find(a => a.id === assetId)?.name || assetId.slice(0, 8)

  const fetchAllAssetRelations = async () => {
    setLoadingRelations(true)
    try {
      const allRelations: any[] = []
      for (const asset of assets) {
        const res = await apiClient.get(`/assets/${asset.id}/relations`)
        if (res.data?.length) {
          for (const r of res.data) {
            if (r.direction === "upstream") {
              allRelations.push({
                ...r,
                source_asset_id: asset.id,
                source_asset_name: asset.name,
                source_asset_type: asset.asset_type,
              })
            } else {
              allRelations.push({
                ...r,
                source_asset_id: r.source_asset_id,
                source_asset_name: r.source_asset_name,
                source_asset_type: r.source_asset_type,
                target_asset_id: asset.id,
                target_asset_name: asset.name,
                target_asset_type: asset.asset_type,
              })
            }
          }
        }
      }
      const uniqueMap = new Map<string, any>()
      allRelations.forEach(r => {
        const key = r.id
        if (!uniqueMap.has(key)) uniqueMap.set(key, r)
      })
      setAssetRelations(Array.from(uniqueMap.values()))
    } catch (err: any) {
      console.error("Failed to fetch asset relations:", err)
    } finally {
      setLoadingRelations(false)
    }
  }

  const fetchRelationTypes = async () => {
    try {
      const res = await apiClient.get("/assets/relation-types")
      setRelationTypes(res.data || [])
    } catch (err: any) {
      console.error("Failed to fetch relation types:", err)
    }
  }

  const handleBatchCreateRelations = async () => {
    if (selectedSourceAssetIds.size === 0 || selectedTargetAssetIds.size === 0) {
      setCreateRelationResult("Select source assets and target assets")
      return
    }
    if (!selectedRelationTypeCode || (selectedRelationTypeCode === "__custom__" && !customRelationText)) {
      setCreateRelationResult("Select or enter a relation type")
      return
    }
    setSaving(true)
    setCreateRelationResult(null)
    let created = 0
    let skipped = 0
    let errors = 0
    try {
      const relationTypeToUse = selectedRelationTypeCode === "__custom__" ? customRelationText : selectedRelationTypeCode
      for (const sourceId of selectedSourceAssetIds) {
        for (const targetId of selectedTargetAssetIds) {
          try {
            await apiClient.post(`/assets/${sourceId}/relations`, {
              target_asset_id: targetId,
              relation_type_code: relationTypeToUse,
            })
            created++
          } catch (err: any) {
            if (err.response?.status === 400 && err.response?.data?.detail?.includes("already exists")) {
              skipped++
            } else {
              errors++
            }
          }
        }
      }
      setCreateRelationResult(`Created: ${created}, Skipped: ${skipped}, Errors: ${errors}`)
      setSelectedSourceAssetIds(new Set())
      setSelectedTargetAssetIds(new Set())
      setSelectedRelationTypeCode("")
      setCustomRelationText("")
      await fetchAllAssetRelations()
    } catch (err: any) {
      setCreateRelationResult(err.response?.data?.detail || "Failed to create relations")
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRelation = async (relationId: string, assetId: string) => {
    if (!confirm("Delete this relation?")) return
    try {
      await apiClient.delete(`/assets/${assetId}/relations/${relationId}`)
      await fetchAllAssetRelations()
    } catch (err: any) {
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to delete relation" })
    }
  }

  const buildRelationTreeForDirection = (direction: "upstream" | "downstream"): TreeNode[] => {
    const directionRelations = assetRelations.filter(r => r.direction === direction)

    const childrenMap = new Map<string, { rel: any; childId: string; childName: string; childType: string }[]>()

    if (direction === "upstream") {
      directionRelations.forEach(rel => {
        const parentId = rel.source_asset_id
        if (!childrenMap.has(parentId)) childrenMap.set(parentId, [])
        childrenMap.get(parentId)!.push({
          rel,
          childId: rel.target_asset_id,
          childName: rel.target_asset_name || "Unknown",
          childType: rel.target_asset_type || "unknown",
        })
      })
    } else {
      directionRelations.forEach(rel => {
        const parentId = rel.target_asset_id
        if (!childrenMap.has(parentId)) childrenMap.set(parentId, [])
        childrenMap.get(parentId)!.push({
          rel,
          childId: rel.source_asset_id,
          childName: rel.source_asset_name || "Unknown",
          childType: rel.source_asset_type || "unknown",
        })
      })
    }

    const buildNode = (
      assetId: string,
      assetName: string,
      assetType: string,
      visitedInPath: Set<string>
    ): TreeNode => {
      const children: TreeNode[] = []
      const childEntries = childrenMap.get(assetId) || []

childEntries.forEach(({ rel, childId, childName, childType }) => {
          const relTypeName = rel.relation_type_info?.name || rel.relation_type || ""
          const relTypeCode = rel.relation_type_info?.code || rel.relation_type

          const childNode: TreeNode = {
            assetId: childId,
            assetName: childName,
            assetType: childType,
            direction,
            relationType: relTypeCode,
            relationTypeName: relTypeName,
            relationId: rel.id,
            children: [],
          }

          if (!visitedInPath.has(childId)) {
            const newVisited = new Set(visitedInPath)
            newVisited.add(childId)
            childNode.children = buildNode(childId, childName, childType, newVisited).children
          }

          children.push(childNode)
        })

      return {
        assetId,
        assetName,
        assetType,
        direction,
        children,
      }
    }

    const groups = new Map<string, typeof directionRelations>()

    if (direction === "upstream") {
      directionRelations.forEach(rel => {
        const rootKey = rel.source_asset_id
        if (!groups.has(rootKey)) groups.set(rootKey, [])
        groups.get(rootKey)!.push(rel)
      })
    } else {
      directionRelations.forEach(rel => {
        const rootKey = rel.target_asset_id
        if (!groups.has(rootKey)) groups.set(rootKey, [])
        groups.get(rootKey)!.push(rel)
      })
    }

    const nodes: TreeNode[] = []
    const processedRoots = new Set<string>()

    groups.forEach((relations, rootId) => {
      if (processedRoots.has(rootId)) return
      processedRoots.add(rootId)

      const firstRel = relations[0]
      let rootName: string
      let rootType: string

      if (direction === "upstream") {
        rootName = firstRel.source_asset_name || "Unknown"
        rootType = firstRel.source_asset_type || "unknown"
      } else {
        rootName = firstRel.target_asset_name || "Unknown"
        rootType = firstRel.target_asset_type || "unknown"
      }

      const node = buildNode(rootId, rootName, rootType, new Set([rootId]))
      nodes.push(node)
    })

    return nodes
  }

  const buildRelationTree = useMemo((): TreeNode[] => {
    const dirMap: Record<string, "upstream" | "downstream" | null> = {
      depends_on: "upstream",
      required_by: "downstream",
      all: null,
    }
    const mappedDir = dirMap[relationTreeDirection]
    if (mappedDir === null) {
      const upstreamNodes = buildRelationTreeForDirection("upstream")
      const downstreamNodes = buildRelationTreeForDirection("downstream")
      return [...upstreamNodes, ...downstreamNodes]
    }
    return buildRelationTreeForDirection(mappedDir)
  }, [assetRelations, relationTreeDirection])

  const treeData = useMemo(() => {
    interface AssetTreeNode {
      id: string
      name: string
      assetType: string
      relationType?: string
      direction?: string
      relationId?: string
      children?: AssetTreeNode[]
    }
    const seenIds = new Map<string, number>()

    const transformNode = (node: TreeNode, parentPath: string = ""): AssetTreeNode => {
      let uniqueSuffix = ""
      const baseId = node.assetId
      if (parentPath) {
        const count = seenIds.get(baseId) || 0
        if (count > 0) {
          uniqueSuffix = `-${count}`
        }
        seenIds.set(baseId, count + 1)
      } else {
        seenIds.set(baseId, 1)
      }

      const id = parentPath ? `${parentPath}-${baseId}${uniqueSuffix}` : baseId

      return {
        id,
        name: node.assetName,
        assetType: node.assetType,
        relationType: node.relationType,
        direction: node.direction,
        relationId: node.relationId,
        children: node.children?.map(child => transformNode(child, id)),
      }
    }
    return buildRelationTree.map(node => transformNode(node))
  }, [buildRelationTree])

  const toggleSourceAsset = (id: string) => {
    const next = new Set(selectedSourceAssetIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedSourceAssetIds(next)
  }

  const toggleTargetAsset = (id: string) => {
    const next = new Set(selectedTargetAssetIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedTargetAssetIds(next)
  }

  const selectAllSource = () => {
    setSelectedSourceAssetIds(new Set(filteredSourceAssets.map(a => a.id)))
  }

  const selectAllTarget = () => {
    setSelectedTargetAssetIds(new Set(filteredTargetAssets.map(a => a.id)))
  }

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">{t("common.loading")}</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t("mappings.title")}</h1>
          <p className="text-muted-foreground mt-1">{t("mappings.subtitle")}</p>
        </div>
        {activeMode && (
          <div className={`px-3 py-1.5 rounded-md text-sm font-semibold border ${approachColorMap[activeMode.security_approach] || ""}`}>
            <Shield className="inline w-4 h-4 mr-1.5" />
            {activeMode.security_approach}
          </div>
        )}
      </div>

      <Tabs value={mainTab} onValueChange={setMainTab}>
        <TabsList>
          <TabsTrigger value="business_processes">{t("mappings.bpTab")}</TabsTrigger>
          <TabsTrigger value="assets">{t("mappings.assetsTab")}</TabsTrigger>
          <TabsTrigger value="asset_relations">{t("mappings.assetRelationsTab")}</TabsTrigger>
        </TabsList>

{/* === Business Processes Tab === */}
        <TabsContent value="business_processes" className="space-y-6">
          {/* Protection mode lock notice */}
          {activeMode && (
            <div className="p-3 rounded-md bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {t("mappings.modeLocked")}
            </div>
          )}

          {/* BP list with protection needs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="w-5 h-5" />
                {t("mappings.protectionNeeds")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bps.map((bp) => (
                  <div key={bp.id} className="p-4 rounded-lg border bg-card">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-sm">{bp.name}</p>
                          {approvedBpIds.has(bp.id) ? (
                            <Badge variant="outline" className="text-green-600 border-green-300 bg-green-50 text-xs gap-1">
                              <CheckCircle2 className="w-3 h-3" /> Approved
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-yellow-600 border-yellow-300 bg-yellow-50 text-xs gap-1">
                              <XCircle className="w-3 h-3" /> Unapproved
                            </Badge>
                          )}
                        </div>
                        <div className="flex gap-3 mt-1">
                          <span className="text-xs">C: <Badge variant="outline" className={`text-xs ${ciaColorMap[bp.confidentiality_need] || ""}`}>{bp.confidentiality_need}</Badge></span>
                          <span className="text-xs">I: <Badge variant="outline" className={`text-xs ${ciaColorMap[bp.integrity_need] || ""}`}>{bp.integrity_need}</Badge></span>
                          <span className="text-xs">A: <Badge variant="outline" className={`text-xs ${ciaColorMap[bp.availability_need] || ""}`}>{bp.availability_need}</Badge></span>
                        </div>
                        {bpMappings.filter(m => m.business_process_id === bp.id).length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {bpMappings.filter(m => m.business_process_id === bp.id).map(m => (
                              <Badge key={m.id} variant="secondary" className="text-xs">
                                {m.module_code}
                                <button
                                  className="ml-1 hover:text-destructive"
                                  onClick={() => handleRemoveBpMapping(m.id)}
                                >
                                  ×
                                </button>
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      {editingBp?.id === bp.id ? (
                        <div className="flex items-center gap-2 shrink-0">
                          <select
                            className="border rounded p-1 text-xs bg-background"
                            value={editForm.confidentiality}
                            onChange={(e) => setEditForm(f => ({ ...f, confidentiality: e.target.value }))}
                          >
                            <option value="normal">normal</option>
                            <option value="high">high</option>
                            <option value="very_high">very_high</option>
                          </select>
                          <select
                            className="border rounded p-1 text-xs bg-background"
                            value={editForm.integrity}
                            onChange={(e) => setEditForm(f => ({ ...f, integrity: e.target.value }))}
                          >
                            <option value="normal">normal</option>
                            <option value="high">high</option>
                            <option value="very_high">very_high</option>
                          </select>
                          <select
                            className="border rounded p-1 text-xs bg-background"
                            value={editForm.availability}
                            onChange={(e) => setEditForm(f => ({ ...f, availability: e.target.value }))}
                          >
                            <option value="normal">normal</option>
                            <option value="high">high</option>
                            <option value="very_high">very_high</option>
                          </select>
                          <div className="flex gap-1">
                            <Button size="sm" onClick={handleSaveProtectionNeed} disabled={saving}>
                              {saving ? t("common.saving") : t("common.save")}
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditingBp(null)}>
                              {t("common.cancel")}
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <Button variant="outline" size="sm" onClick={() => handleEditProtectionNeed(bp)}>
                          {t("mappings.editProtectionNeed")}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Map module to BP */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Link2 className="w-5 h-5" />
                {t("mappings.mapModule")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{t("mappings.businessProcess")}</label>
                <select
                  className="w-full border rounded-md p-2 bg-background"
                  value={bpTargetId}
                  onChange={(e) => setBpTargetId(e.target.value)}
                >
                  <option value="">{t("mappings.selectTarget")}</option>
                  {bps.map((bp) => (
                    <option key={bp.id} value={bp.id}>{bp.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t("mappings.moduleName")}</label>
                <select
                  className="w-full border rounded-md p-2 bg-background"
                  value={bpModuleId}
                  onChange={(e) => setBpModuleId(e.target.value)}
                >
                  <option value="">{t("mappings.selectModule")}</option>
                  {modules.map((mod) => (
                    <option key={mod.id} value={mod.id}>
                      {mod.code} — {mod.name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                className="w-full"
                onClick={handleMapModuleToBp}
                disabled={saving || !bpTargetId || !bpModuleId}
              >
                {saving ? t("common.saving") : t("mappings.mapToScope")}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* === Assets Tab === */}
        <TabsContent value="assets" className="space-y-4">
          <div className="grid grid-cols-12 gap-6">
            {/* Asset list with type tabs */}
            <Card className="lg:col-span-5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{t("mappings.assetsTab")}</CardTitle>
                  {filteredAssets.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={handleSelectAll} className="text-xs">
                      <CheckSquare className="w-3.5 h-3.5 mr-1" />
                      {selectedAssetIds.size === filteredAssets.length ? "Deselect all" : "Select all"}
                    </Button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {ASSET_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => { setAssetTypeTab(type); setSelectedAssetIds(new Set()) }}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        assetTypeTab === type
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      {type === "all" ? t("mappings.allTypes") : t(`mappings.${type}`)} ({typeCounts[type] || 0})
                    </button>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="max-h-[400px] overflow-y-auto space-y-1">
                {filteredAssets.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">{t("mappings.noMappings")}</p>
                ) : (
                  filteredAssets.map((asset) => (
                    <label
                      key={asset.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-accent ${
                        selectedAssetIds.has(asset.id) ? "border-primary bg-primary/5" : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        checked={selectedAssetIds.has(asset.id)}
                        onChange={() => handleToggleAsset(asset.id)}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{asset.name}</p>
                        <p className="text-xs text-muted-foreground">{asset.asset_type?.replace(/_/g, " ")}</p>
                        {asset.person_id && personMap[asset.person_id] && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {personMap[asset.person_id]}
                          </p>
                        )}
                      </div>
                      {asset.linked_processes && asset.linked_processes.length > 0 && (
                        asset.linked_processes.length === 1 ? (
                          <span className="text-xs text-muted-foreground shrink-0 max-w-[180px] truncate" title={asset.linked_processes[0].name}>
                            {asset.linked_processes[0].name}
                          </span>
                        ) : (
                          <Badge variant="outline" className="text-xs shrink-0">
                            {asset.linked_processes.length} BP
                          </Badge>
                        )
                      )}
                    </label>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Right: Scope Mapping panel */}
            <Card className="lg:col-span-7">
              <Tabs value={scopeTab} onValueChange={(v) => setScopeTab(v as "select" | "mapped")}>
                <CardHeader className="pb-3">
                  <TabsList className="w-full">
                    <TabsTrigger value="select" className="flex-1">{t("mappings.mapModule")}</TabsTrigger>
                    <TabsTrigger value="mapped" className="flex-1">{t("mappings.mappedModules")}</TabsTrigger>
                  </TabsList>
                </CardHeader>
                <CardContent>
                  <TabsContent value="select" className="mt-0">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-muted-foreground">{filteredModules.length} modules, {selectedModuleIds.size} selected</span>
                        <button
                          className={`text-xs px-2 py-0.5 rounded ${moduleSort === "code" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"}`}
                          onClick={() => setModuleSort("code")}
                        >
                          Code
                        </button>
                        <button
                          className={`text-xs px-2 py-0.5 rounded ${moduleSort === "name" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"}`}
                          onClick={() => setModuleSort("name")}
                        >
                          Name
                        </button>
                        <button
                          className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground hover:bg-accent ml-auto"
                          onClick={() => {
                            if (selectedModuleIds.size === filteredModules.length) {
                              setSelectedModuleIds(new Set())
                            } else {
                              setSelectedModuleIds(new Set(filteredModules.map(m => m.id)))
                            }
                          }}
                        >
                          {selectedModuleIds.size === filteredModules.length ? "Deselect all" : "Select all"}
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-1 mb-2">
                        {(["all", ...MODULE_GROUPS] as const).map((g) => (
                          <button
                            key={g}
                            onClick={() => setModuleGroupFilter(g)}
                            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                              moduleGroupFilter === g
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground hover:bg-accent"
                            }`}
                          >
                            {g === "all" ? "All" : g} ({moduleGroupCounts[g] || 0})
                          </button>
                        ))}
                      </div>
                      <div className="max-h-[300px] overflow-y-auto space-y-1 border rounded-md p-1">
                        {filteredModules.map((mod) => (
                          <label
                              key={mod.id}
                              className={`flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer ${
                                selectedModuleIds.has(mod.id) ? "bg-primary/5 border border-primary/30" : "border border-transparent"
                              }`}
                            >
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                                checked={selectedModuleIds.has(mod.id)}
                                onChange={() => {
                                  const next = new Set(selectedModuleIds)
                                  if (next.has(mod.id)) next.delete(mod.id)
                                  else next.add(mod.id)
                                  setSelectedModuleIds(next)
                                }}
                              />
                            <span className="font-mono text-xs text-muted-foreground w-16 shrink-0">{mod.code}</span>
                            <span className="text-sm truncate flex-1">{mod.name}</span>
                            <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{mod.module_group}</span>
                          </label>
                        ))}
                      </div>
                      {batchResult && (
                        <div className={`p-3 rounded-md text-sm border ${
                          batchResult.includes("failed") || batchResult.includes("Errors:")
                            ? "bg-red-50 border-red-200 text-red-700"
                            : "bg-green-50 border-green-200 text-green-700"
                        }`}>
                          {batchResult}
                        </div>
                      )}
                      <Button
                        className="w-full"
                        onClick={handleBatchMap}
                        disabled={saving || selectedAssetIds.size === 0 || selectedModuleIds.size === 0}
                      >
                        {saving ? t("common.saving") : `${t("mappings.mapSelected")} (${selectedModuleIds.size} mod × ${selectedAssetIds.size} assets)`}
                      </Button>
                    </div>
                  </TabsContent>
                  <TabsContent value="mapped" className="mt-0">
                    {selectedAssetIds.size === 0 ? (
                      <p className="text-sm text-muted-foreground py-8 text-center">{t("mappings.noSelection")}</p>
                    ) : availableGroups.length === 0 ? (
                      <p className="text-sm text-muted-foreground py-8 text-center">{t("mappings.noMappings")}</p>
                    ) : (
                      <>
                        <Tabs value={activeModuleGroup} onValueChange={setModuleGroupTab}>
                          <TabsList className="flex-wrap h-auto mb-3">
                            {availableGroups.map((group) => (
                              <TabsTrigger key={group} value={group} className="text-xs">
                                {group} ({mappingsByGroup[group]?.length || 0})
                              </TabsTrigger>
                            ))}
                          </TabsList>
                          {availableGroups.map((group) => (
                            <TabsContent key={group} value={group} className="space-y-2 mt-0">
                              {mappingsByGroup[group]?.map((m) => (
                                <div key={m.id} className="flex items-center justify-between p-3 rounded-lg border bg-card">
                                  <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium truncate">
                                      <span className="font-mono text-xs text-muted-foreground">{m.module?.code}</span>{" "}
                                      {m.module?.name}
                                    </p>
                                    <p className="text-xs text-muted-foreground truncate">
                                      {t("mappings.target")}: {getAssetName(m.asset_id)}
                                    </p>
                                  </div>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-destructive shrink-0 ml-2"
                                    onClick={() => handleRemoveAssetMapping(m.id)}
                                  >
                                    <Unlink className="w-4 h-4" />
                                  </Button>
                                </div>
                              ))}
                              {(!mappingsByGroup[group] || mappingsByGroup[group].length === 0) && (
                                <p className="text-sm text-muted-foreground py-4 text-center">No mappings in this group</p>
                              )}
                            </TabsContent>
                          ))}
                        </Tabs>
                      </>
                    )}
                  </TabsContent>
                </CardContent>
              </Tabs>
            </Card>
          </div>
        </TabsContent>

        {/* === Cross-linked Tab === */}
        <TabsContent value="asset_relations" className="space-y-4">
          <div className="grid grid-cols-12 gap-6">
            {/* Source Assets */}
            <Card className="lg:col-span-6">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{t("mappings.sourceAssets")}</CardTitle>
                  {filteredSourceAssets.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={selectAllSource} className="text-xs">
                      <CheckSquare className="w-3.5 h-3.5 mr-1" />
                      {selectedSourceAssetIds.size === filteredSourceAssets.length ? "Deselect all" : "Select all"}
                    </Button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {ASSET_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => { setSourceAssetTypeTab(type); setSelectedSourceAssetIds(new Set()) }}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        sourceAssetTypeTab === type ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      {type === "all" ? t("mappings.allTypes") : t(`mappings.${type}`)} ({sourceTypeCounts[type] || 0})
                    </button>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="max-h-[400px] overflow-y-auto space-y-1">
                {filteredSourceAssets.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">{t("mappings.noAssets")}</p>
                ) : (
                  filteredSourceAssets.map((asset) => (
                    <label
                      key={asset.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-accent ${
                        selectedSourceAssetIds.has(asset.id) ? "border-primary bg-primary/5" : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        checked={selectedSourceAssetIds.has(asset.id)}
                        onChange={() => toggleSourceAsset(asset.id)}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{asset.name}</p>
                        <p className="text-xs text-muted-foreground">{asset.asset_type?.replace(/_/g, " ")}</p>
                        {asset.person_id && personMap[asset.person_id] && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {personMap[asset.person_id]}
                          </p>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Target Assets */}
            <Card className="lg:col-span-6">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{t("mappings.targetAssets")}</CardTitle>
                  {filteredTargetAssets.length > 0 && (
                    <Button variant="ghost" size="sm" onClick={selectAllTarget} className="text-xs">
                      <CheckSquare className="w-3.5 h-3.5 mr-1" />
                      {selectedTargetAssetIds.size === filteredTargetAssets.length ? "Deselect all" : "Select all"}
                    </Button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {ASSET_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => { setTargetAssetTypeTab(type); setSelectedTargetAssetIds(new Set()) }}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        targetAssetTypeTab === type ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      {type === "all" ? t("mappings.allTypes") : t(`mappings.${type}`)} ({targetTypeCounts[type] || 0})
                    </button>
                  ))}
                </div>
              </CardHeader>
              <CardContent className="max-h-[400px] overflow-y-auto space-y-1">
                {filteredTargetAssets.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">{t("mappings.noAssets")}</p>
                ) : (
                  filteredTargetAssets.map((asset) => (
                    <label
                      key={asset.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors hover:bg-accent ${
                        selectedTargetAssetIds.has(asset.id) ? "border-primary bg-primary/5" : ""
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        checked={selectedTargetAssetIds.has(asset.id)}
                        onChange={() => toggleTargetAsset(asset.id)}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{asset.name}</p>
                        <p className="text-xs text-muted-foreground">{asset.asset_type?.replace(/_/g, " ")}</p>
                        {asset.person_id && personMap[asset.person_id] && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {personMap[asset.person_id]}
                          </p>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Create Relations Card - only shown when source AND target selected */}
          {selectedSourceAssetIds.size > 0 && selectedTargetAssetIds.size > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{t("mappings.createRelations")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <p className="text-sm text-muted-foreground">
                    {selectedSourceAssetIds.size} source × {selectedTargetAssetIds.size} target = <span className="font-semibold text-primary">{selectedSourceAssetIds.size * selectedTargetAssetIds.size}</span> relations to create
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">{t("mappings.relationType")}</label>
                    <select
                      className="w-full border rounded-md p-2 bg-background text-sm"
                      value={selectedRelationTypeCode}
                      onChange={(e) => { setSelectedRelationTypeCode(e.target.value); setCustomRelationText(""); }}
                    >
                      <option value="">{t("common.selectRelationType")}</option>
                      {relationTypes.map((rt: any) => (
                        <option key={rt.code} value={rt.code}>
                          {rt.name} ({rt.code})
                        </option>
                      ))}
                      <option value="__custom__">{t("mappings.customRelationType")}</option>
                    </select>
                    {selectedRelationTypeCode && selectedRelationTypeCode !== "__custom__" && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {relationTypes.find((rt: any) => rt.code === selectedRelationTypeCode)?.description}
                      </p>
                    )}
                  </div>
                  {selectedRelationTypeCode === "__custom__" && (
                    <div>
                      <label className="block text-sm font-medium mb-1">{t("mappings.customRelationType")}</label>
                      <input
                        type="text"
                        className="w-full border rounded-md p-2 bg-background text-sm"
                        value={customRelationText}
                        onChange={(e) => setCustomRelationText(e.target.value)}
                        placeholder={t("mappings.customRelationPlaceholder")}
                      />
                    </div>
                  )}
                </div>
                {createRelationResult && (
                  <div className={`p-3 rounded-md text-sm ${
                    createRelationResult.includes("Error") ? "bg-red-50 text-red-700 border border-red-200" : "bg-green-50 text-green-700 border border-green-200"
                  }`}>
                    {createRelationResult}
                  </div>
                )}
                <div className="flex justify-end">
                  <Button
                    onClick={handleBatchCreateRelations}
                    disabled={saving || (!selectedRelationTypeCode || (selectedRelationTypeCode === "__custom__" && !customRelationText))}
                  >
                    {saving ? t("common.saving") : t("mappings.createRelations")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Existing Relations */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{t("mappings.existingRelations")}</CardTitle>
                <div className="flex items-center gap-4">
                  {relationViewMode === "tree" && (
                    <div className="flex gap-1">
                      {(["depends_on", "required_by", "all"] as const).map((dir) => (
                        <button
                          key={dir}
                          onClick={() => setRelationTreeDirection(dir)}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            relationTreeDirection === dir ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                          }`}
                        >
                          {dir === "depends_on" ? t("assets.upstream") : dir === "required_by" ? t("assets.downstream") : t("mappings.all")}
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-1 bg-muted rounded-md p-1">
                    <button
                      onClick={() => setRelationViewMode("list")}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        relationViewMode === "list" ? "bg-background shadow-sm" : "hover:bg-background/50"
                      }`}
                    >
                      {t("mappings.listView") || "List"}
                    </button>
                    <button
                      onClick={() => setRelationViewMode("tree")}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1 ${
                        relationViewMode === "tree" ? "bg-background shadow-sm" : "hover:bg-background/50"
                      }`}
                    >
                      <GitBranch className="h-3 w-3" />
                      {t("mappings.treeView") || "Tree"}
                    </button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loadingRelations ? (
                <div className="flex items-center gap-2 text-muted-foreground py-8">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t("common.loading")}
                </div>
              ) : filteredRelations.length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">{t("mappings.noRelations")}</p>
              ) : relationViewMode === "tree" ? (
                <div className="max-h-[500px] overflow-y-auto border rounded-lg p-4 bg-card">
                  <Tree
                    data={treeData}
                    height={450}
                    width={800}
                    disableDrag
                    disableDrop
                  >
                    {({ node, style }: NodeRendererProps<any>) => (
                      <div
                        style={style}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-md border bg-background hover:bg-accent cursor-pointer group"
                      >
                        <span className={`w-2 h-2 rounded-full shrink-0 ${node.data.direction === "upstream" ? "bg-blue-500" : "bg-purple-500"}`} />
                        <span className="text-sm font-medium truncate">{node.data.name}</span>
                        <Badge variant="outline" className="text-xs shrink-0">{node.data.assetType}</Badge>
                        {node.data.relationType && (
                          <Badge variant="secondary" className="text-xs opacity-70 shrink-0">{node.data.relationType}</Badge>
                        )}
                        {node.data.relationId && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-destructive opacity-0 group-hover:opacity-100 ml-auto shrink-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteRelation(node.data.relationId, node.id)
                            }}
                          >
                            <Unlink className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    )}
                  </Tree>
                </div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {filteredRelations.map((rel: any) => (
                    <div key={rel.id} className="flex items-center justify-between p-3 rounded-lg border bg-card">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className={rel.direction === "upstream" ? "bg-blue-50 dark:bg-blue-900" : "bg-purple-50 dark:bg-purple-900"}>
                          {rel.direction === "upstream" ? t("assets.upstream") : t("assets.downstream")}
                        </Badge>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{rel.source_asset_name}</span>
                          <span className="text-xs text-muted-foreground">──{rel.relation_type_info?.code || rel.relation_type}──</span>
                          <span className="text-sm font-medium">
                            {rel.direction === "upstream" ? rel.target_asset_name : rel.source_asset_name}
                          </span>
                        </div>
                        {rel.description && (
                          <span className="text-xs text-muted-foreground">({rel.description})</span>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive shrink-0"
                        onClick={() => handleDeleteRelation(rel.id, rel.direction === "upstream" ? rel.source_asset_id : rel.target_asset_id)}
                      >
                        <Unlink className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

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
