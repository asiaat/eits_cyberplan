import { useState, useEffect, useRef, useMemo } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Link2, Unlink, AlertTriangle, Shield, CheckCircle2, XCircle, CheckSquare } from "lucide-react"

interface LinkedProcess {
  id: string
  name: string
  status: string
}

interface AssetItem {
  id: string
  name: string
  asset_type: string
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

const ASSET_TYPES = ["all", "information_asset", "software", "hardware", "service", "data", "other"] as const

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

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
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

  useEffect(() => { orgRef.current = selectedOrgId }, [selectedOrgId])

  const activeMode = protectionMode?.is_active ? protectionMode : null

  const fetchData = async () => {
    if (!selectedOrgId) return
    setLoading(true)
    try {
      const [assetsRes, bpsRes, modulesRes, assetMapRes, bpMapRes, modeRes, pnRes] = await Promise.all([
        apiClient.get("/assets/"),
        apiClient.get("/business-processes/"),
        apiClient.get("/catalog/modules"),
        apiClient.get("/asset-module-mappings/"),
        apiClient.get("/modeling/bp-mappings"),
        apiClient.get("/protection-mode/"),
        apiClient.get("/eits/protection-needs"),
      ])
      setAssets(assetsRes.data || [])
      setBps(bpsRes.data || [])
      setModules(modulesRes.data || [])
      setAssetMappings(assetMapRes.data || [])
      setBpMappings(bpMapRes.data || [])
      setProtectionNeeds(pnRes.data || [])
      const active = (modeRes.data || []).find((m: ProtectionModeItem) => m.is_active)
      setProtectionMode(active || null)
    } catch {
      alert("Failed to load data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [selectedOrgId])

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
      alert("Select both a BP and a module")
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
      alert(err.response?.data?.detail || "Failed to map module")
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
      alert(err.response?.data?.detail || "Failed to remove mapping")
    }
  }

  const handleRemoveBpMapping = async (id: string) => {
    if (!confirm("Remove this module from scope?")) return
    try {
      await apiClient.delete(`/modeling/map/${id}`, { params: { target_type: "business_process" } })
      await fetchData()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to remove mapping")
    }
  }

  const handleEditProtectionNeed = (bp: BpItem) => {
    if (activeMode) {
      alert(t("mappings.modeLocked"))
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
      alert(err.response?.data?.detail || "Failed to update protection needs")
    } finally {
      setSaving(false)
    }
  }

  const getAssetName = (assetId: string) => assets.find(a => a.id === assetId)?.name || assetId.slice(0, 8)

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
          <TabsTrigger value="assets">{t("mappings.assetsTab")}</TabsTrigger>
          <TabsTrigger value="business_processes">{t("mappings.bpTab")}</TabsTrigger>
        </TabsList>

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
                      </div>
                      {asset.linked_processes && asset.linked_processes.length > 0 && (
                        <Badge variant="outline" className="text-xs shrink-0">
                          {asset.linked_processes.length} BP
                        </Badge>
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
                        {/* Show mapped modules for this BP */}
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
      </Tabs>
    </div>
  )
}
