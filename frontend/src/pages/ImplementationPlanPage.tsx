import { useState, useEffect, useMemo } from "react"
import { ImrTable } from "@/components/imr/ImrTable"
import { ImrItemModal } from "@/components/imr/ImrItemModal"
import { ImrDashboardStats, StatsFilter } from "@/components/imr/ImrDashboardStats"
import { SnapshotSelector } from "@/components/imr/SnapshotSelector"
import { ImrItem, IMR_STATUS_OPTIONS, IMR_PRIORITY_OPTIONS } from "@/lib/imr-types"
import { useTranslation } from "@/lib/i18n"
import { useImrApi } from "@/lib/use-imr-api"
import { apiClient } from "@/lib/api-client"
import { List, LayoutGrid, BarChart3, ShieldAlert, CheckSquare, X } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

const MODULE_GROUPS = ["All", "ISMS", "ORP", "CON", "OPS", "DER", "INF", "NET", "SYS", "APP", "IND"]

type ViewMode = "list" | "grouped" | "bulk"

export default function ImplementationPlanPage() {
  const { t } = useTranslation()
  const [selectedItem, setSelectedItem] = useState<ImrItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [activeTab, setActiveTab] = useState("All")
  const [showStats, setShowStats] = useState(() => {
    const stored = localStorage.getItem("eits-imr-show-stats")
    return stored !== "false"
  })
  const [filter, setFilter] = useState<{
    pearo_status?: string
    priority?: string
    overdue_only?: boolean
  }>({})
  const [statsFilter, setStatsFilter] = useState<StatsFilter>(null)
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null)
  const [hasActivePlan, setHasActivePlan] = useState<boolean | null>(null)

  // Multi-select bulk edit state
  const [selectedItemIds, setSelectedItemIds] = useState<Set<string>>(new Set())
  const [selectedItems, setSelectedItems] = useState<ImrItem[]>([])
  const [showBulkEdit, setShowBulkEdit] = useState(false)
  const [bulkUpdating, setBulkUpdating] = useState(false)
  const [bulkEditFormData, setBulkEditFormData] = useState<Record<string, any>>({})
  const [availableUsers, setAvailableUsers] = useState<{ id: string; full_name: string }[]>([])
  const [errorDialog, setErrorDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })

  useEffect(() => {
    apiClient.get("/protection-mode/active")
      .then(() => setHasActivePlan(true))
      .catch(() => setHasActivePlan(false))
  }, [])

  useEffect(() => {
    if (showBulkEdit) {
      loadUsers()
    }
  }, [showBulkEdit])

  const loadUsers = async () => {
    try {
      const res = await apiClient.get("/users/")
      setAvailableUsers(res.data || [])
    } catch {
      // silent
    }
  }

  const handleEditItem = (item: ImrItem) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedItem(null)
  }

  const { exportImrItems, bulkUpdateItems, loading: exporting, error: exportError } = useImrApi()

  const handleSaveItem = (updatedItem: ImrItem) => {
    console.log("Item saved:", updatedItem.id)
  }

  const handleExport = () => {
    exportImrItems(filter)
  }

  const handleStatsFilterChange = (newFilter: StatsFilter) => {
    setStatsFilter(newFilter)
    setFilter((prev) => {
      if (!newFilter) {
        if (prev.priority && prev.pearo_status) return prev
        return { ...prev, priority: undefined, pearo_status: undefined }
      }
      if (newFilter.type === "priority") {
        return { ...prev, priority: prev.priority === newFilter.value ? undefined : newFilter.value, pearo_status: undefined }
      }
      if (newFilter.type === "pearo_status") {
        return { ...prev, pearo_status: prev.pearo_status === newFilter.value ? undefined : newFilter.value, priority: undefined }
      }
      return prev
    })
  }

  const toggleStats = () => {
    setShowStats((prev) => {
      const next = !prev
      localStorage.setItem("eits-imr-show-stats", String(next))
      return next
    })
  }

  // Multi-select handlers
  const handleToggleSelect = (id: string) => {
    setSelectedItemIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSelectAll = (itemIds: string[]) => {
    setSelectedItemIds(prev => {
      if (prev.size > 0 && prev.size === itemIds.length) return new Set()
      return new Set(itemIds)
    })
  }

  const handleClearSelection = () => {
    setSelectedItemIds(new Set())
  }

  const handleBulkUpdate = async () => {
    if (selectedItemIds.size === 0) return
    setBulkUpdating(true)
    try {
      const updates: Record<string, any> = {}
      for (const [key, value] of Object.entries(bulkEditFormData)) {
        if (value !== "" && value !== undefined && value !== null) {
          updates[key] = value
        }
      }
      if (Object.keys(updates).length === 0) {
        setErrorDialog({ open: true, message: "No fields selected for update" })
        setBulkUpdating(false)
        return
      }
      const success = await bulkUpdateItems(Array.from(selectedItemIds), updates)
      if (success) {
        setShowBulkEdit(false)
        handleClearSelection()
        setBulkEditFormData({})
        window.location.reload()
      } else {
        const msg = typeof exportError === "string" ? exportError : JSON.stringify(exportError)
        setErrorDialog({ open: true, message: msg || "Bulk update failed" })
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === "string" ? detail : JSON.stringify(detail)
      setErrorDialog({ open: true, message: msg || "Bulk update failed" })
    } finally {
      setBulkUpdating(false)
    }
  }

  const imrFilters = useMemo(() => {
    if (viewMode === "grouped") {
      return { ...filter, module_group: activeTab === "All" ? undefined : activeTab, snapshot_id: selectedSnapshotId || undefined }
    }
    return { ...filter, snapshot_id: selectedSnapshotId || undefined }
  }, [filter, activeTab, selectedSnapshotId, viewMode])

  return (
    <div>
      {/* Page Header */}
      <div className="mb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {t("implementationPlan.pageTitle")}
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            {t("implementationPlan.pageSubtitle")}
          </p>
          {hasActivePlan === false && !selectedSnapshotId && (
            <div className="mt-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800">
              <div className="flex items-start gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
                    {t("implementationPlan.noActivePlan")}
                  </p>
                  <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                    {t("implementationPlan.noActivePlanDesc")}
                  </p>
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    {t("implementationPlan.viewSnapshotsHint")}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Snapshot Selector */}
          <SnapshotSelector
            selectedSnapshotId={selectedSnapshotId}
            onSelectSnapshot={setSelectedSnapshotId}
          />

          {/* Stats Toggle */}
          <button
            onClick={toggleStats}
            className={`p-2 rounded-md transition-colors ${
              showStats
                ? "bg-background shadow-sm text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
            title={showStats ? "Hide statistics" : "Show statistics"}
          >
            <BarChart3 className="w-4 h-4" />
          </button>

          {/* View Toggle */}
          <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 rounded-md transition-colors ${
                viewMode === "list"
                  ? "bg-background shadow-sm text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("grouped")}
              className={`p-2 rounded-md transition-colors ${
                viewMode === "grouped"
                  ? "bg-background shadow-sm text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title="Group by module"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("bulk")}
              className={`p-2 rounded-md transition-colors ${
                viewMode === "bulk"
                  ? "bg-background shadow-sm text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              title={t("implementationPlan.bulkEdit")}
            >
              <CheckSquare className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {exporting ? t("common.loading") : t("implementationPlan.exportExcel")}
          </button>
        </div>
      </div>

      {/* Error display */}
      {exportError && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
          {typeof exportError === "string" ? exportError : JSON.stringify(exportError)}
        </div>
      )}

      {/* IMR content - hidden when no active plan unless viewing a snapshot */}
      {(hasActivePlan !== false || selectedSnapshotId) && (
        <>
          {showStats && <ImrDashboardStats activeFilter={statsFilter} onFilterChange={handleStatsFilterChange} />}

          <div className="mb-3 bg-card rounded-lg border border-border p-3">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1">
                  {t("implementationPlan.dashboard.filterByStatusLabel")}
                </label>
                <select
                  value={filter.pearo_status || ""}
                  onChange={(e) => {
                    setFilter({ ...filter, pearo_status: e.target.value || undefined })
                    setStatsFilter(null)
                  }}
                  className="border border-border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 bg-background"
                >
                  <option value="">{t("implementationPlan.dashboard.allStatuses")}</option>
                  {IMR_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {t(option.labelKey)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1">
                  {t("implementationPlan.dashboard.overdueSection")}
                </label>
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    checked={filter.overdue_only || false}
                    onChange={(e) => setFilter({ ...filter, overdue_only: e.target.checked || undefined })}
                    className="rounded border-border text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-muted-foreground">{t("implementationPlan.dashboard.showOverdueOnly")}</span>
                </label>
              </div>

              {(filter.pearo_status || filter.overdue_only) && (
                <button
                  onClick={() => {
                    setFilter({})
                    setStatsFilter(null)
                  }}
                  className="text-sm text-indigo-600 hover:text-indigo-900 underline"
                >
                  {t("implementationPlan.dashboard.clearFilters")}
                </button>
              )}
            </div>
          </div>

          {/* Selection bar */}
          {viewMode === "bulk" && selectedItemIds.size > 0 && (
            <div className="mb-3 space-y-2">
              <div className="flex items-center justify-between bg-primary/5 border border-primary/20 rounded-lg px-4 py-3">
                <span className="text-sm font-medium">
                  {t("implementationPlan.selectedCount", { count: selectedItemIds.size })}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowBulkEdit(true)}
                    className="px-3 py-1.5 rounded-md bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 transition-colors"
                  >
                    {t("implementationPlan.bulkEdit")}
                  </button>
                  <button
                    onClick={handleClearSelection}
                    className="px-3 py-1.5 rounded-md text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900 transition-colors"
                  >
                    {t("implementationPlan.clearSelection")}
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedItems.map(item => (
                  <span
                    key={item.id}
                    className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 border border-primary/20 px-3 py-1.5 text-sm font-medium"
                  >
                    {item.measure?.code || item.id}
                    <button
                      onClick={() => handleToggleSelect(item.id)}
                      className="rounded-full p-0.5 hover:bg-primary/20 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {viewMode === "grouped" && (
            <div className="mb-4 overflow-x-auto">
              <div className="flex gap-1 min-w-max border-b">
                {MODULE_GROUPS.map((group) => (
                  <button
                    key={group}
                    onClick={() => {
                      setActiveTab(group)
                    }}
                    className={`px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                      activeTab === group
                        ? "border-b-2 border-primary text-primary"
                        : "text-muted-foreground hover:text-foreground border-b-2 border-transparent"
                    }`}
                  >
                    {group}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
            <ImrTable
              onEditItem={selectedSnapshotId ? undefined : handleEditItem}
              readOnly={!!selectedSnapshotId}
              filters={imrFilters}
              selectionMode={viewMode === "bulk"}
              selectedIds={selectedItemIds}
              onToggleSelect={handleToggleSelect}
              onSelectAll={handleSelectAll}
              onSelectionChanged={setSelectedItems}
            />
          </div>
        </>
      )}

      {/* IMR Item Modal */}
      <ImrItemModal
        item={selectedItem}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveItem}
      />

      {/* Bulk Edit Dialog */}
      <Dialog open={showBulkEdit} onOpenChange={setShowBulkEdit} modal={false}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("implementationPlan.bulkEditTitle")}</DialogTitle>
            <DialogDescription>
              {t("implementationPlan.bulkEditDesc", { count: selectedItemIds.size })}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.pearoStatus")}</label>
              <select
                value={bulkEditFormData.pearo_status || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, pearo_status: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="">{t("implementationPlan.noChange")}</option>
                {IMR_STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{t(opt.labelKey)}</option>
                ))}
              </select>
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.bulkPriority")}</label>
              <select
                value={bulkEditFormData.priority || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, priority: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="">{t("implementationPlan.noChange")}</option>
                {IMR_PRIORITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{t(opt.labelKey)}</option>
                ))}
              </select>
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.responsiblePerson")}</label>
              <select
                value={bulkEditFormData.responsible_user_id || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, responsible_user_id: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="">{t("implementationPlan.noChange")}</option>
                {availableUsers.map((user) => (
                  <option key={user.id} value={user.id}>{user.full_name}</option>
                ))}
              </select>
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.dueDate")}</label>
              <input
                type="date"
                value={bulkEditFormData.due_date || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, due_date: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              />
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.verificationMethod")}</label>
              <input
                type="text"
                value={bulkEditFormData.verification_method || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, verification_method: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
                placeholder={t("implementationPlan.verifMethodPlaceholder")}
              />
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.requirementProfile")}</label>
              <input
                type="text"
                value={bulkEditFormData.requirement_profile || ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, requirement_profile: e.target.value || undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
                placeholder={t("implementationPlan.reqProfilePlaceholder")}
              />
            </div>
            <div>
               <label className="text-sm font-medium">{t("implementationPlan.cost")}</label>
              <input
                type="number"
                value={bulkEditFormData.cost_eur ?? ""}
                onChange={(e) => setBulkEditFormData(prev => ({ ...prev, cost_eur: e.target.value ? Number(e.target.value) : undefined }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
                placeholder={t("implementationPlan.costPlaceholder")}
              />
            </div>
          </div>
          <DialogFooter>
            <button
              onClick={() => setShowBulkEdit(false)}
              disabled={bulkUpdating}
              className="px-4 py-2 rounded-md border border-input text-sm font-medium hover:bg-muted transition-colors"
            >
              {t("common.cancel")}
            </button>
            <button
              onClick={handleBulkUpdate}
              disabled={bulkUpdating}
              className="px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {bulkUpdating ? t("implementationPlan.updating") : t("implementationPlan.updateItems", { count: selectedItemIds.size })}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Error dialog */}
      <Dialog open={errorDialog.open} onOpenChange={(open) => setErrorDialog(prev => ({ ...prev, open }))}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>{errorDialog.message}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              onClick={() => setErrorDialog({ open: false, message: "" })}
              className="px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              OK
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}