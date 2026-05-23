import { useState } from "react"
import { ImrTable } from "@/components/imr/ImrTable"
import { ImrItemModal } from "@/components/imr/ImrItemModal"
import { ImrDashboardStats } from "@/components/imr/ImrDashboardStats"
import { ImrItem, IMR_STATUS_OPTIONS } from "@/lib/imr-types"
import { useTranslation } from "@/lib/i18n"
import { useImrApi } from "@/lib/use-imr-api"
import { List, LayoutGrid } from "lucide-react"

const MODULE_GROUPS = ["All", "ISMS", "ORP", "CON", "OPS", "DER", "INF", "NET", "SYS", "APP", "IND"]

type ViewMode = "list" | "grouped"

export default function ImplementationPlanPage() {
  const { t } = useTranslation()
  const [selectedItem, setSelectedItem] = useState<ImrItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [activeTab, setActiveTab] = useState("All")
  const [filter, setFilter] = useState<{
    pearo_status?: string
    priority?: string
    overdue_only?: boolean
  }>({})

  const handleEditItem = (item: ImrItem) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedItem(null)
  }

  const { exportImrItems, loading: exporting, error: exportError } = useImrApi()

  const handleSaveItem = (updatedItem: ImrItem) => {
    console.log("Item saved:", updatedItem.id)
  }

  const handleExport = () => {
    exportImrItems(filter)
  }

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
        </div>
        <div className="flex items-center gap-3">
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

      {/* Dashboard Statistics */}
      <ImrDashboardStats />

      {/* Filter Bar */}
      <div className="mb-3 bg-card rounded-lg border border-border p-3">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1">
              {t("implementationPlan.dashboard.filterByStatusLabel")}
            </label>
            <select
              value={filter.pearo_status || ""}
              onChange={(e) => setFilter({ ...filter, pearo_status: e.target.value || undefined })}
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
              onClick={() => setFilter({})}
              className="text-sm text-indigo-600 hover:text-indigo-900 underline"
            >
              {t("implementationPlan.dashboard.clearFilters")}
            </button>
          )}
        </div>
      </div>

      {/* Error display */}
      {exportError && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
          {exportError}
        </div>
      )}

      {/* Grouped View - Tab Bar */}
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

      {/* IMR Table */}
      <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
        <ImrTable
          onEditItem={handleEditItem}
          filters={viewMode === "grouped" ? { ...filter, module_group: activeTab === "All" ? undefined : activeTab } : filter}
        />
      </div>

      {/* IMR Item Modal */}
      <ImrItemModal
        item={selectedItem}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveItem}
      />
    </div>
  )
}