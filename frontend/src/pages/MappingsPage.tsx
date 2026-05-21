import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Layers, Link2, Unlink, AlertTriangle, Shield, CheckCircle2, XCircle } from "lucide-react"

interface AssetItem {
  id: string
  name: string
  asset_type: string
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

const approachColorMap: Record<string, string> = {
  BASIC: "bg-green-100 text-green-800 border-green-200",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200",
  CORE: "bg-red-100 text-red-800 border-red-200",
}

export default function MappingsPage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const orgRef = useRef(selectedOrgId)

  const [targetType, setTargetType] = useState<"asset" | "business_process">("asset")
  const [targetId, setTargetId] = useState("")
  const [moduleId, setModuleId] = useState("")

  const [assets, setAssets] = useState<AssetItem[]>([])
  const [bps, setBps] = useState<BpItem[]>([])
  const [modules, setModules] = useState<ModuleItem[]>([])
  const [assetMappings, setAssetMappings] = useState<AssetMappingItem[]>([])
  const [bpMappings, setBpMappings] = useState<BpMappingItem[]>([])
  const [protectionMode, setProtectionMode] = useState<ProtectionModeItem | null>(null)
  const [protectionNeeds, setProtectionNeeds] = useState<ProtectionNeedItem[]>([])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingBp, setEditingBp] = useState<BpItem | null>(null)
  const [editForm, setEditForm] = useState({ confidentiality: "", integrity: "", availability: "" })

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

  const handleMapModule = async () => {
    if (!targetId || !moduleId) {
      alert("Please select both a target and a module")
      return
    }
    setSaving(true)
    try {
      await apiClient.post("/modeling/map", null, {
        params: { module_id: moduleId, target_type: targetType, target_id: targetId },
      })
      setTargetId("")
      setModuleId("")
      await fetchData()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to map module")
    } finally {
      setSaving(false)
    }
  }

  const handleRemoveMapping = async (id: string, type: "asset" | "business_process") => {
    if (!confirm("Remove this module from scope?")) return
    try {
      await apiClient.delete(`/modeling/map/${id}`, { params: { target_type: type } })
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

  const selectedTargets = targetType === "asset" ? assets : bps

  const approvedBpIds = new Set([
    ...protectionNeeds.filter((pn) => pn.approved_by).map((pn) => pn.business_process_id),
    ...bps.filter((bp: any) =>
      bp.confidentiality_need !== null && bp.confidentiality_need !== "" && bp.confidentiality_need !== "unknown" ||
      bp.integrity_need !== null && bp.integrity_need !== "" && bp.integrity_need !== "unknown" ||
      bp.availability_need !== null && bp.availability_need !== "" && bp.availability_need !== "unknown"
    ).map((bp: any) => bp.id)
  ])

  const linkedProcesses = assets.find((a) => a.id === targetId) as any
  const linkedProcessList: Array<{ id: string; name: string; status: string }> = linkedProcesses?.linked_processes || []

  const allApproved = linkedProcessList.length > 0 && linkedProcessList.every((lp) => approvedBpIds.has(lp.id))

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map New Module */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Link2 className="w-5 h-5" />
              {t("mappings.mapModule")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t("mappings.targetType")}</label>
              <div className="flex gap-2">
                <Button
                  variant={targetType === "asset" ? "default" : "outline"}
                  size="sm"
                  onClick={() => { setTargetType("asset"); setTargetId("") }}
                >
                  {t("mappings.asset")}
                </Button>
                <Button
                  variant={targetType === "business_process" ? "default" : "outline"}
                  size="sm"
                  onClick={() => { setTargetType("business_process"); setTargetId("") }}
                >
                  {t("mappings.businessProcess")}
                </Button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">{t("mappings.targetType")}</label>
              <select
                className="w-full border rounded-md p-2 bg-background"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
              >
                <option value="">{t("mappings.selectTarget")}</option>
                {selectedTargets.map((item: any) => (
                  <option key={item.id} value={item.id}>
                    {item.name} {item.asset_type ? `(${item.asset_type})` : ""}
                  </option>
                ))}
              </select>
            </div>

            {targetType === "asset" && targetId && (
              <div className="rounded-md border p-3 space-y-2 bg-muted/30">
                <p className="text-xs font-semibold text-muted-foreground uppercase">{t("mappings.linkedProcesses")}</p>
                {linkedProcessList.length === 0 ? (
                  <div className="flex items-center gap-2 text-sm text-destructive">
                    <XCircle className="w-4 h-4" />
                    <span>No linked business processes</span>
                  </div>
                ) : (
                  linkedProcessList.map((lp) => (
                    <div key={lp.id} className="flex items-center justify-between text-sm">
                      <span>{lp.name}</span>
                      {approvedBpIds.has(lp.id) ? (
                        <Badge variant="outline" className="text-green-600 border-green-300 bg-green-50 gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Approved
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-yellow-600 border-yellow-300 bg-yellow-50 gap-1">
                          <AlertTriangle className="w-3 h-3" /> Not approved
                        </Badge>
                      )}
                    </div>
                  ))
                )}
                {linkedProcessList.length > 0 && (
                  <div className={`flex items-center gap-2 text-sm pt-2 border-t ${allApproved ? "text-green-600" : "text-yellow-600"}`}>
                    {allApproved ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span className="font-medium">{allApproved ? "Ready for modeling" : "Cannot model — unapproved protection needs"}</span>
                  </div>
                )}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1">{t("mappings.moduleName")}</label>
              <select
                className="w-full border rounded-md p-2 bg-background"
                value={moduleId}
                onChange={(e) => setModuleId(e.target.value)}
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
              onClick={handleMapModule}
              disabled={saving || !targetId || !moduleId}
            >
              {saving ? t("common.saving") : t("mappings.mapToScope")}
            </Button>
          </CardContent>
        </Card>

        {/* Mapped Modules */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Layers className="w-5 h-5" />
              {t("mappings.mappedModules")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {assetMappings.length === 0 && bpMappings.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("mappings.noMappings")}</p>
            ) : (
              <>
                {assetMappings.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">{t("mappings.asset")}</p>
                    {assetMappings.map((m) => (
                      <div key={m.id} className="flex items-center justify-between p-3 rounded-lg border mb-2 bg-card">
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">
                            <span className="font-mono text-xs text-muted-foreground">{m.module?.code}</span>{" "}
                            {m.module?.name}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {t("mappings.target")}: {assets.find(a => a.id === m.asset_id)?.name || m.asset_id}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive shrink-0"
                          onClick={() => handleRemoveMapping(m.id, "asset")}
                        >
                          <Unlink className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                {bpMappings.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">{t("mappings.businessProcess")}</p>
                    {bpMappings.map((m) => (
                      <div key={m.id} className="flex items-center justify-between p-3 rounded-lg border mb-2 bg-card">
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">
                            <span className="font-mono text-xs text-muted-foreground">{m.module_code}</span>{" "}
                            {m.module_name}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {t("mappings.target")}: {m.business_process_name}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive shrink-0"
                          onClick={() => handleRemoveMapping(m.id, "business_process")}
                        >
                          <Unlink className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Business Process Protection Needs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="w-5 h-5" />
            {t("mappings.protectionNeeds")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeMode && (
            <div className="mb-4 p-3 rounded-md bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {t("mappings.modeLocked")}
            </div>
          )}
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
                        <span className="text-xs">
                          C: <Badge variant="outline" className="text-xs">{bp.confidentiality_need}</Badge>
                        </span>
                        <span className="text-xs">
                          I: <Badge variant="outline" className="text-xs">{bp.integrity_need}</Badge>
                        </span>
                        <span className="text-xs">
                          A: <Badge variant="outline" className="text-xs">{bp.availability_need}</Badge>
                        </span>
                      </div>
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
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditProtectionNeed(bp)}
                    >
                      {t("mappings.editProtectionNeed")}
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
