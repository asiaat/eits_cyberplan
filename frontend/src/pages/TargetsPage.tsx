import React, { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiClient } from "@/lib/api-client"
import { Search, ChevronDown, ChevronRight, Target, Plus, Trash2, BookOpen, X, Loader2 } from "lucide-react"

interface TargetObject {
  id: string
  tenant_id: string
  name: string
  asset_type: string
  description: string | null
  remarks: string | null
  criticality: string
  is_grouped: boolean
  quantity: number
  group_name: string | null
  confidentiality_need: string
  integrity_need: string
  availability_need: string
  lifecycle_status: string
  owner_user_id: string | null
  person_id: string | null
  linked_process_count: number
  module_mapping_count: number
  imr_item_count: number
  created_at: string
}

interface TargetModule {
  id: string
  module_id: string
  module_code: string
  module_name: string
  module_group: string
  justification: string | null
  modeled_by: string | null
  modeled_at: string | null
  imr_item_count: number
  imr_status_summary: {
    P: number
    E: number
    A: number
    R: number
    O: number
  }
}

interface EitsModule {
  id: string
  code: string
  name: string
  module_group: string
}

const typeColors: Record<string, string> = {
  APP: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200",
  SYS: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200",
  NET: "bg-teal-100 text-teal-800 border-teal-200 dark:bg-teal-900 dark:text-teal-200",
  INF: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200",
  IND: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200",
}

const criticalityColors: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200",
  normal: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200",
  low: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200",
}

const TARGET_TYPES = ["APP", "SYS", "NET", "INF", "IND"]
const CRITICALITY_LEVELS = ["low", "normal", "high", "critical"]

export default function TargetsPage() {
  const { t } = useTranslation()
  const [targets, setTargets] = useState<TargetObject[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [expandedTargets, setExpandedTargets] = useState<Set<string>>(new Set())
  const [targetModules, setTargetModules] = useState<Record<string, TargetModule[]>>({})
  const [loadingModules, setLoadingModules] = useState<Record<string, boolean>>({})

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [moduleDialogOpen, setModuleDialogOpen] = useState(false)
  const [selectedTarget, setSelectedTarget] = useState<TargetObject | null>(null)
  const [saving, setSaving] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    target_type: "SYS" as string,
    group_name: "",
    quantity: 1,
    description: "",
    remarks: "",
    criticality: "normal",
  })

  // Module search state
  const [moduleSearch, setModuleSearch] = useState("")
  const [availableModules, setAvailableModules] = useState<EitsModule[]>([])
  const [loadingModulesList, setLoadingModulesList] = useState(false)
  const [moduleJustification, setModuleJustification] = useState("")

  useEffect(() => {
    fetchTargets()
  }, [])

  const fetchTargets = async () => {
    try {
      const response = await apiClient.get("/targets")
      setTargets(response.data)
    } catch (error) {
      console.error("Failed to fetch targets:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTargetModules = async (targetId: string) => {
    if (targetModules[targetId]) return

    setLoadingModules(prev => ({ ...prev, [targetId]: true }))
    try {
      const response = await apiClient.get(`/targets/${targetId}/modules`)
      setTargetModules(prev => ({ ...prev, [targetId]: response.data }))
    } catch (error) {
      console.error("Failed to fetch target modules:", error)
    } finally {
      setLoadingModules(prev => ({ ...prev, [targetId]: false }))
    }
  }

  const toggleTarget = (targetId: string) => {
    const newExpanded = new Set(expandedTargets)
    if (newExpanded.has(targetId)) {
      newExpanded.delete(targetId)
    } else {
      newExpanded.add(targetId)
      fetchTargetModules(targetId)
    }
    setExpandedTargets(newExpanded)
  }

  const filteredTargets = targets.filter(target =>
    target.name.toLowerCase().includes(search.toLowerCase()) ||
    (target.group_name && target.group_name.toLowerCase().includes(search.toLowerCase()))
  )

  const handleCreateTarget = async () => {
    setSaving(true)
    try {
      await apiClient.post("/targets", {
        name: formData.name,
        target_type: formData.target_type,
        group_name: formData.group_name || null,
        quantity: formData.quantity,
        description: formData.description || null,
        remarks: formData.remarks || null,
        criticality: formData.criticality,
        is_grouped: true,
      })
      setCreateDialogOpen(false)
      resetForm()
      fetchTargets()
    } catch (error) {
      console.error("Failed to create target:", error)
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateTarget = async () => {
    if (!selectedTarget) return
    setSaving(true)
    try {
      await apiClient.put(`/targets/${selectedTarget.id}`, {
        name: formData.name,
        target_type: formData.target_type,
        group_name: formData.group_name || null,
        quantity: formData.quantity,
        description: formData.description || null,
        remarks: formData.remarks || null,
        criticality: formData.criticality,
      })
      setEditDialogOpen(false)
      setSelectedTarget(null)
      resetForm()
      fetchTargets()
    } catch (error) {
      console.error("Failed to update target:", error)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteTarget = async (targetId: string) => {
    if (!confirm(t("targets.confirmDelete"))) return
    try {
      await apiClient.delete(`/targets/${targetId}`)
      fetchTargets()
    } catch (error) {
      console.error("Failed to delete target:", error)
    }
  }

  const openEditDialog = (target: TargetObject) => {
    setSelectedTarget(target)
    setFormData({
      name: target.name,
      target_type: target.asset_type,
      group_name: target.group_name || "",
      quantity: target.quantity,
      description: target.description || "",
      remarks: target.remarks || "",
      criticality: target.criticality,
    })
    setEditDialogOpen(true)
  }

  const openModuleDialog = (target: TargetObject) => {
    setSelectedTarget(target)
    setModuleSearch("")
    setModuleJustification("")
    setAvailableModules([])
    setModuleDialogOpen(true)
  }

  const searchModules = async (query: string) => {
    if (query.length < 2) return
    setLoadingModulesList(true)
    try {
      const response = await apiClient.get("/catalog/modules", { params: { search: query } })
      setAvailableModules(response.data.slice(0, 20))
    } catch (error) {
      console.error("Failed to search modules:", error)
    } finally {
      setLoadingModulesList(false)
    }
  }

  const handleAddModule = async (moduleId: string) => {
    if (!selectedTarget) return
    try {
      await apiClient.post(`/targets/${selectedTarget.id}/modules`, {
        module_id: moduleId,
        justification: moduleJustification || null,
      })
      setModuleDialogOpen(false)
      setModuleJustification("")
      fetchTargetModules(selectedTarget.id)
      fetchTargets()
    } catch (error) {
      console.error("Failed to add module:", error)
    }
  }

  const handleRemoveModule = async (targetId: string, mappingId: string) => {
    if (!confirm(t("targets.confirmRemoveModule"))) return
    try {
      await apiClient.delete(`/targets/${targetId}/modules/${mappingId}`)
      fetchTargetModules(targetId)
      fetchTargets()
    } catch (error) {
      console.error("Failed to remove module:", error)
    }
  }

  const resetForm = () => {
    setFormData({
      name: "",
      target_type: "SYS",
      group_name: "",
      quantity: 1,
      description: "",
      remarks: "",
      criticality: "normal",
    })
  }

  const getImrStatusBadge = (summary: TargetModule["imr_status_summary"]) => {
    const total = summary.P + summary.E + summary.A + summary.R + summary.O
    if (total === 0) return null

    return (
      <div className="flex gap-1 text-xs">
        {summary.P > 0 && <span className="px-1 bg-gray-100 rounded">{summary.P} P</span>}
        {summary.E > 0 && <span className="px-1 bg-red-100 text-red-700 rounded">{summary.E} E</span>}
        {summary.A > 0 && <span className="px-1 bg-green-100 text-green-700 rounded">{summary.A} A</span>}
        {summary.R > 0 && <span className="px-1 bg-yellow-100 text-yellow-700 rounded">{summary.R} R</span>}
      </div>
    )
  }

  if (loading) {
    return <div className="text-center py-12 text-muted-foreground">{t("common.loading")}</div>
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Target className="h-8 w-8"  />
            {t("targets.title")}
          </h1>
          <p className="text-muted-foreground mt-1">
            {targets.length} {t("targets.totalTargets")}
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2"  />
          {t("targets.createTarget")}
        </Button>
      </div>

      <div className="mb-6">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"  />
          <Input
            placeholder={t("targets.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
           />
        </div>
      </div>

      {filteredTargets.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {search ? t("targets.noResults") : t("targets.noData")}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTargets.map((target) => {
            const isExpanded = expandedTargets.has(target.id)
            const modules = targetModules[target.id] || []

            return (
              <Card key={target.id} className="overflow-hidden">
                <div
                  className="flex items-center gap-4 px-6 py-4 bg-muted/30 hover:bg-muted/50 cursor-pointer"
                  onClick={() => toggleTarget(target.id)}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-5 w-5 text-muted-foreground"  />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-muted-foreground"  />
                  )}
                  <Badge className={typeColors[target.asset_type] || "bg-gray-100"}>
                    {target.asset_type}
                  </Badge>
                  <div className="flex-1">
                    <span className="font-medium">{target.name}</span>
                    {target.group_name && (
                      <span className="text-sm text-muted-foreground ml-2">
                        ({target.group_name})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className={criticalityColors[target.criticality] || criticalityColors.normal}>
                      {t(`assets.criticalityLevels.${target.criticality}`) || target.criticality}
                    </Badge>
                    <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900">
                      {target.quantity} {t("targets.quantity")}
                    </Badge>
                    <Badge variant="outline" className="bg-purple-50 dark:bg-purple-900">
                      {target.module_mapping_count} {t("targets.mappings")}
                    </Badge>
                    <Badge variant="outline" className="bg-green-50 dark:bg-green-900">
                      {target.imr_item_count} {t("targets.imrItems")}
                    </Badge>
                  </div>
                </div>

                {isExpanded && (
                  <CardContent className="border-t">
                    <div className="flex justify-end gap-2 mb-4">
                      <Button size="sm" variant="outline" onClick={() => openEditDialog(target)}>
                        {t("common.edit")}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => openModuleDialog(target)}>
                        <BookOpen className="h-4 w-4 mr-1"  />
                        {t("targets.addModule")}
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDeleteTarget(target.id)}>
                        <Trash2 className="h-4 w-4"  />
                      </Button>
                    </div>

                    {target.description && (
                      <p className="text-sm text-muted-foreground mb-4">{target.description}</p>
                    )}

                    {loadingModules[target.id] ? (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin"  />
                        {t("common.loading")}
                      </div>
                    ) : modules.length > 0 ? (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">{t("targets.mappedModules")}</h4>
                        {modules.map((mod) => (
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
                            <div className="flex items-center gap-3">
                              {getImrStatusBadge(mod.imr_status_summary)}
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-500 hover:text-red-700"
                                onClick={() => handleRemoveModule(target.id, mod.id)}
                              >
                                <X className="h-4 w-4"  />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">{t("targets.noModules")}</p>
                    )}
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Target Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{t("targets.createTarget")}</DialogTitle>
            <DialogDescription>{t("targets.createTargetDesc")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t("targets.name")} *</Label>
              <Input
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, name: e.target.value })}
                placeholder={t("targets.namePlaceholder")}
               />
            </div>
            <div>
              <Label>{t("targets.type")} *</Label>
              <Select
                value={formData.target_type}
                onValueChange={(value) => setFormData({ ...formData, target_type: value })}
              >
                <SelectTrigger>
                  <SelectValue  />
                </SelectTrigger>
                <SelectContent>
                  {TARGET_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {t(`targets.targetTypes.${type}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("targets.groupName")}</Label>
              <Input
                value={formData.group_name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, group_name: e.target.value })}
                placeholder={t("targets.groupNamePlaceholder")}
               />
            </div>
            <div>
              <Label>{t("targets.quantity")}</Label>
              <Input
                type="number"
                min={1}
                value={formData.quantity}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
               />
            </div>
            <div>
              <Label>{t("assets.criticality")}</Label>
              <Select
                value={formData.criticality}
                onValueChange={(value) => setFormData({ ...formData, criticality: value })}
              >
                <SelectTrigger>
                  <SelectValue  />
                </SelectTrigger>
                <SelectContent>
                  {CRITICALITY_LEVELS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {t(`assets.criticalityLevels.${level}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("assets.description")}</Label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, description: e.target.value })}
                placeholder={t("assets.description")}
               />
            </div>
            <div>
              <Label>{t("assets.remarks")}</Label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.remarks}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, remarks: e.target.value })}
                placeholder={t("assets.remarksPlaceholder")}
               />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={handleCreateTarget} disabled={saving || !formData.name}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin"  /> : t("common.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Target Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{t("targets.editTarget")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t("targets.name")} *</Label>
              <Input
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, name: e.target.value })}
               />
            </div>
            <div>
              <Label>{t("targets.type")} *</Label>
              <Select
                value={formData.target_type}
                onValueChange={(value) => setFormData({ ...formData, target_type: value })}
              >
                <SelectTrigger>
                  <SelectValue  />
                </SelectTrigger>
                <SelectContent>
                  {TARGET_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {t(`targets.targetTypes.${type}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("targets.groupName")}</Label>
              <Input
                value={formData.group_name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, group_name: e.target.value })}
               />
            </div>
            <div>
              <Label>{t("targets.quantity")}</Label>
              <Input
                type="number"
                min={1}
                value={formData.quantity}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
               />
            </div>
            <div>
              <Label>{t("assets.criticality")}</Label>
              <Select
                value={formData.criticality}
                onValueChange={(value) => setFormData({ ...formData, criticality: value })}
              >
                <SelectTrigger>
                  <SelectValue  />
                </SelectTrigger>
                <SelectContent>
                  {CRITICALITY_LEVELS.map((level) => (
                    <SelectItem key={level} value={level}>
                      {t(`assets.criticalityLevels.${level}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>{t("assets.description")}</Label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, description: e.target.value })}
               />
            </div>
            <div>
              <Label>{t("assets.remarks")}</Label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.remarks}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, remarks: e.target.value })}
               />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={handleUpdateTarget} disabled={saving || !formData.name}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin"  /> : t("common.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Module Dialog */}
      <Dialog open={moduleDialogOpen} onOpenChange={setModuleDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("targets.addModule")}</DialogTitle>
            <DialogDescription>
              {selectedTarget && t("targets.addModuleDesc", { target: selectedTarget.name })}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t("targets.searchModule")}</Label>
              <Input
                value={moduleSearch}
                onChange={(e) => {
                  setModuleSearch(e.target.value)
                  searchModules(e.target.value)
                }}
                placeholder={t("targets.searchModulePlaceholder")}
               />
            </div>
            <div>
              <Label>{t("targets.justification")}</Label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={moduleJustification}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setModuleJustification(e.target.value)}
                placeholder={t("targets.justificationPlaceholder")}
               />
            </div>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {loadingModulesList ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin"  />
                  {t("common.loading")}
                </div>
              ) : availableModules.length > 0 ? (
                availableModules.map((mod) => (
                  <div
                    key={mod.id}
                    className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 cursor-pointer"
                    onClick={() => handleAddModule(mod.id)}
                  >
                    <div>
                      <code className="text-sm font-mono">{mod.code}</code>
                      <span className="text-sm ml-2">{mod.name}</span>
                    </div>
                    <Badge variant="outline">{mod.module_group}</Badge>
                  </div>
                ))
              ) : moduleSearch.length >= 2 ? (
                <p className="text-sm text-muted-foreground">{t("targets.noModulesFound")}</p>
              ) : (
                <p className="text-sm text-muted-foreground">{t("targets.typeToSearch")}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModuleDialogOpen(false)}>
              {t("common.cancel")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}