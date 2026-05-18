import { useState, useEffect, useMemo } from "react"
import { useTranslation } from "@/lib/i18n"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { apiClient } from "@/lib/api-client"
import {
  ChevronDown,
  ChevronRight,
  Search,
} from "lucide-react"

interface CatalogVersion {
  id: string
  version: string
  year: string
  name: string
  source_name: string | null
  source_file_hash: string | null
  imported_at: string | null
  active: boolean
  is_active: boolean
  released_at: string | null
}

interface EitsModule {
  id: string
  catalog_version_id: string
  code: string
  name: string
  module_group: string | null
  category: string | null
  description: string | null
  module_type: string | null
  source_url: string | null
}

interface EitsCatalogMeasure {
  id: string
  module_id: string
  code: string
  name: string
  measure_level: string
  description: string | null
  responsible_role: string | null
}

interface ModuleWithMeasures extends EitsModule {
  measures: EitsCatalogMeasure[]
}

const levelColors: Record<string, string> = {
  BASE: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200 dark:border-green-800",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-800",
  HIGH: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200 dark:border-red-800",
}

const moduleTypeColors: Record<string, string> = {
  PROCESS: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-800",
  SYSTEM: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-800",
}

const groupColors: Record<string, string> = {
  ISMS: "bg-cyan-100 text-cyan-800 border-cyan-200 dark:bg-cyan-900 dark:text-cyan-200",
  ORP: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200",
  CON: "bg-pink-100 text-pink-800 border-pink-200 dark:bg-pink-900 dark:text-pink-200",
  OPS: "bg-teal-100 text-teal-800 border-teal-200 dark:bg-teal-900 dark:text-teal-200",
  DER: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900 dark:text-amber-200",
  INF: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200",
  NET: "bg-indigo-100 text-indigo-800 border-indigo-200 dark:bg-indigo-900 dark:text-indigo-200",
  SYS: "bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-200",
  APP: "bg-violet-100 text-violet-800 border-violet-200 dark:bg-violet-900 dark:text-violet-200",
  IND: "bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-900 dark:text-rose-200",
}

const GROUPS = ["ISMS", "ORP", "CON", "OPS", "DER", "INF", "NET", "SYS", "APP", "IND"]
const LEVELS = ["BASE", "STANDARD", "HIGH"]
const MODULE_TYPES = ["PROCESS", "SYSTEM"]

export default function CatalogPage() {
  const { t } = useTranslation()

  const [versions, setVersions] = useState<CatalogVersion[]>([])
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"modules" | "measures" | "versions">("measures")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState("")
  const [groupFilter, setGroupFilter] = useState<string>("all")
  const [typeFilter, setTypeFilter] = useState<string>("all")
  const [levelFilter, setLevelFilter] = useState<string>("all")

  const [modules, setModules] = useState<EitsModule[]>([])
  const [measures, setMeasures] = useState<EitsCatalogMeasure[]>([])
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set())
  const [expandedMeasures, setExpandedMeasures] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchVersions()
  }, [])

  useEffect(() => {
    if (selectedVersionId) {
      if (activeTab === "modules" || activeTab === "measures") {
        fetchModules()
      }
      if (activeTab === "measures") {
        fetchMeasures()
      }
    }
  }, [selectedVersionId, activeTab])

  const fetchVersions = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get("/catalog/versions")
      setVersions(response.data)
      if (response.data.length > 0 && !selectedVersionId) {
        setSelectedVersionId(response.data[0].id)
      }
    } catch (err) {
      console.error("Failed to fetch versions:", err)
      setError("Failed to load catalog versions")
    } finally {
      setLoading(false)
    }
  }

  const fetchModules = async () => {
    if (!selectedVersionId) return
    try {
      const params: Record<string, string> = {}
      if (groupFilter !== "all") params.module_group = groupFilter
      if (typeFilter !== "all") params.module_type = typeFilter
      const response = await apiClient.get(`/catalog/versions/${selectedVersionId}/modules`, { params })
      setModules(response.data)
    } catch (err) {
      console.error("Failed to fetch modules:", err)
    }
  }

  const fetchMeasures = async () => {
    if (!selectedVersionId) return
    try {
      const params: Record<string, string> = { version_id: selectedVersionId }
      if (groupFilter !== "all") params.module_group = groupFilter
      if (levelFilter !== "all") params.level = levelFilter
      const response = await apiClient.get("/catalog/measures", { params })
      setMeasures(response.data)
    } catch (err) {
      console.error("Failed to fetch measures:", err)
    }
  }

  const modulesWithMeasures = useMemo<ModuleWithMeasures[]>(() => {
    return modules.map((mod) => ({
      ...mod,
      measures: measures.filter((m) => m.module_id === mod.id),
    }))
  }, [modules, measures])

  const filteredModules = useMemo(() => {
    return modulesWithMeasures.filter(
      (mod) =>
        mod.code.toLowerCase().includes(search.toLowerCase()) ||
        mod.name.toLowerCase().includes(search.toLowerCase())
    )
  }, [modulesWithMeasures, search])

  const toggleModuleExpand = (moduleId: string) => {
    const newExpanded = new Set(expandedModules)
    if (newExpanded.has(moduleId)) {
      newExpanded.delete(moduleId)
    } else {
      newExpanded.add(moduleId)
    }
    setExpandedModules(newExpanded)
  }

  const toggleMeasureExpand = (measureId: string) => {
    const newExpanded = new Set(expandedMeasures)
    if (newExpanded.has(measureId)) {
      newExpanded.delete(measureId)
    } else {
      newExpanded.add(measureId)
    }
    setExpandedMeasures(newExpanded)
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">{t("catalog.title")}</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{t("catalog.selectVersion")}:</span>
          <Select value={selectedVersionId || ""} onValueChange={setSelectedVersionId}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder={t("catalog.selectVersion")} />
            </SelectTrigger>
            <SelectContent>
              {versions.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.year} - {v.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex gap-1 mb-6 border-b">
        <button
          onClick={() => setActiveTab("modules")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "modules"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t("catalog.tabs.modules")}
        </button>
        <button
          onClick={() => setActiveTab("measures")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "measures"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t("catalog.tabs.measures")}
        </button>
        <button
          onClick={() => setActiveTab("versions")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "versions"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t("catalog.tabs.versions")}
        </button>
      </div>

      <div className="mb-4 flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("catalog.filters.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={groupFilter} onValueChange={setGroupFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder={t("catalog.filters.group")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("catalog.filters.all")}</SelectItem>
            {GROUPS.map((g) => (
              <SelectItem key={g} value={g}>
                {t(`catalog.groups.${g}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(activeTab === "modules") && (
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder={t("catalog.filters.type")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("catalog.filters.all")}</SelectItem>
              {MODULE_TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {activeTab === "measures" && (
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder={t("catalog.filters.level")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("catalog.filters.all")}</SelectItem>
              {LEVELS.map((l) => (
                <SelectItem key={l} value={l}>
                  {t(`catalog.levels.${l.toLowerCase()}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">{t("common.loading")}</div>
      ) : error ? (
        <div className="text-center py-12 text-destructive">{error}</div>
      ) : activeTab === "versions" ? (
        <VersionsTab versions={versions} />
      ) : activeTab === "modules" ? (
        <ModulesTab
          modules={filteredModules}
          expandedModules={expandedModules}
          toggleModuleExpand={toggleModuleExpand}
        />
      ) : (
        <MeasuresTab
          modulesWithMeasures={filteredModules}
          expandedModules={expandedModules}
          expandedMeasures={expandedMeasures}
          toggleModuleExpand={toggleModuleExpand}
          toggleMeasureExpand={toggleMeasureExpand}
        />
      )}
    </div>
  )
}

function VersionsTab({ versions }: { versions: CatalogVersion[] }) {
  const { t } = useTranslation()

  if (versions.length === 0) {
    return <div className="text-center py-12 text-muted-foreground">{t("catalog.noVersions")}</div>
  }

  return (
    <div className="border rounded-lg">
      <table className="w-full">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.year")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.name")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.code")}</th>
            <th className="px-4 py-3 text-center text-sm font-medium">{t("catalog.columns.active")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.importedAt")}</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {versions.map((version) => (
            <tr key={version.id} className="hover:bg-muted/30">
              <td className="px-4 py-3 text-sm">{version.year}</td>
              <td className="px-4 py-3 text-sm font-medium">{version.name}</td>
              <td className="px-4 py-3 text-sm text-muted-foreground">{version.version}</td>
              <td className="px-4 py-3 text-center">
                {version.is_active ? (
                  <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                    {t("common.active")}
                  </Badge>
                ) : (
                  <Badge variant="secondary">{t("common.inactive")}</Badge>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-muted-foreground">
                {version.imported_at ? new Date(version.imported_at).toLocaleDateString() : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ModulesTab({
  modules,
  expandedModules,
  toggleModuleExpand,
}: {
  modules: ModuleWithMeasures[]
  expandedModules: Set<string>
  toggleModuleExpand: (id: string) => void
}) {
  const { t } = useTranslation()

  if (modules.length === 0) {
    return <div className="text-center py-12 text-muted-foreground">{t("catalog.noModules")}</div>
  }

  return (
    <div className="border rounded-lg">
      <table className="w-full">
        <thead className="bg-muted/50">
          <tr>
            <th className="w-10 px-4 py-3"></th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.code")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.name")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.group")}</th>
            <th className="px-4 py-3 text-left text-sm font-medium">{t("catalog.columns.type")}</th>
            <th className="px-4 py-3 text-right text-sm font-medium">{t("catalog.moduleDetail.measureCount")}</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {modules.map((mod) => {
            const isExpanded = expandedModules.has(mod.id)
            return (
              <>
                <tr
                  key={mod.id}
                  className="hover:bg-muted/30 cursor-pointer"
                  onClick={() => toggleModuleExpand(mod.id)}
                >
                  <td className="px-4 py-3">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono">{mod.code}</td>
                  <td className="px-4 py-3 text-sm font-medium">{mod.name}</td>
                  <td className="px-4 py-3">
                    {mod.module_group && (
                      <Badge
                        className={groupColors[mod.module_group] || "bg-gray-100 text-gray-800"}
                      >
                        {mod.module_group}
                      </Badge>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {mod.module_type && (
                      <Badge
                        className={moduleTypeColors[mod.module_type] || "bg-gray-100 text-gray-800"}
                      >
                        {mod.module_type}
                      </Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-muted-foreground">
                    {mod.measures.length}
                  </td>
                </tr>
                {isExpanded && (
                  <tr key={`${mod.id}-expanded`}>
                    <td colSpan={6} className="px-4 py-4 bg-muted/20">
                      <div className="space-y-2">
                        {mod.description && (
                          <div>
                            <span className="text-sm font-medium">{t("catalog.moduleDetail.description")}:</span>
                            <p className="text-sm text-muted-foreground mt-1">{mod.description}</p>
                          </div>
                        )}
                        <div className="flex gap-4 text-sm">
                          <span>
                            <span className="font-medium">{t("catalog.moduleDetail.measureCount")}:</span> {mod.measures.length}
                          </span>
                          {mod.source_url && (
                            <span>
                              <span className="font-medium">{t("catalog.moduleDetail.source")}:</span> RIA
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function MeasuresTab({
  modulesWithMeasures,
  expandedModules,
  expandedMeasures,
  toggleModuleExpand,
  toggleMeasureExpand,
}: {
  modulesWithMeasures: ModuleWithMeasures[]
  expandedModules: Set<string>
  expandedMeasures: Set<string>
  toggleModuleExpand: (id: string) => void
  toggleMeasureExpand: (id: string) => void
}) {
  const { t } = useTranslation()

  const totalMeasures = modulesWithMeasures.reduce((sum, m) => sum + m.measures.length, 0)
  if (modulesWithMeasures.length === 0) {
    return <div className="text-center py-12 text-muted-foreground">{t("catalog.noMeasures")}</div>
  }

  return (
    <div className="space-y-2">
      <div className="text-sm text-muted-foreground mb-4">
        {modulesWithMeasures.length} modules, {totalMeasures} measures total
      </div>
      {modulesWithMeasures.map((mod) => {
        const isModuleExpanded = expandedModules.has(mod.id)
        return (
          <div key={mod.id} className="border rounded-lg overflow-hidden">
            <div
              className="flex items-center gap-3 px-4 py-3 bg-muted/30 hover:bg-muted/50 cursor-pointer"
              onClick={() => toggleModuleExpand(mod.id)}
            >
              {isModuleExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <Badge className={groupColors[mod.module_group || ""] || "bg-gray-100"}>
                {mod.module_group}
              </Badge>
              <span className="font-mono text-sm">{mod.code}</span>
              <span className="font-medium">{mod.name}</span>
              <Badge variant="secondary" className="ml-auto">
                {mod.measures.length} {t("catalog.tabs.measures").toLowerCase()}
              </Badge>
            </div>
            {isModuleExpanded && mod.measures.length > 0 && (
              <div className="divide-y">
                {mod.measures.map((measure) => {
                  const isMeasureExpanded = expandedMeasures.has(measure.id)
                  return (
                    <>
                      <div
                        key={measure.id}
                        className="flex items-center gap-3 px-4 py-2 hover:bg-muted/20 cursor-pointer pl-8"
                        onClick={() => toggleMeasureExpand(measure.id)}
                      >
                        <Badge className={levelColors[measure.measure_level] || "bg-gray-100"}>
                          {t(`catalog.levels.${measure.measure_level.toLowerCase()}`)}
                        </Badge>
                        <span className="font-mono text-sm w-32">{measure.code}</span>
                        <span className="flex-1 text-sm truncate">{measure.name}</span>
                        <span className="text-sm text-muted-foreground w-48 text-right">
                          {measure.responsible_role || "-"}
                        </span>
                      </div>
                      {isMeasureExpanded && (
                        <div className="px-4 py-3 bg-muted/10 pl-16">
                          <div className="space-y-2 text-sm">
                            <div>
                              <span className="font-medium">{t("catalog.measureDetail.description")}:</span>
                              <p className="text-muted-foreground mt-1">{measure.description || "-"}</p>
                            </div>
                            <div className="flex gap-6">
                              <span>
                                <span className="font-medium">{t("catalog.measureDetail.level")}:</span>{" "}
                                <Badge className={levelColors[measure.measure_level]}>
                                  {measure.measure_level}
                                </Badge>
                              </span>
                              <span>
                                <span className="font-medium">{t("catalog.measureDetail.responsible")}:</span>{" "}
                                {measure.responsible_role || "-"}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}