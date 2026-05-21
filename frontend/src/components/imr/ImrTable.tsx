import { useState, useEffect } from "react"
import { ImrItem, ImrValidationStatus } from "@/lib/imr-types"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { ImrStatusBadge, ImrPriorityBadge, ImrValidationIndicator } from "./ImrStatusBadge"

interface ImrTableProps {
  onEditItem?: (item: ImrItem) => void
  filters?: {
    pearo_status?: string
    priority?: string
    asset_id?: string
    overdue_only?: boolean
  }
}

export function ImrTable({ onEditItem, filters }: ImrTableProps) {
  const { t } = useTranslation()
  const { loading, error, fetchImrItems } = useImrApi()
  const [items, setItems] = useState<ImrItem[]>([])
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ImrValidationStatus>>({})
  
  const PAGE_SIZE = 20
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  useEffect(() => {
    loadItems()
  }, [filters, page])

  const loadItems = async () => {
    const skip = (page - 1) * PAGE_SIZE
    const fetchedItems = await fetchImrItems({ ...filters, skip, limit: PAGE_SIZE })
    setItems(fetchedItems)
    setHasMore(fetchedItems.length === PAGE_SIZE)
    
    const statuses: Record<string, ImrValidationStatus> = {}
    for (const item of fetchedItems) {
      if (item.pearo_status !== "R") {
        statuses[item.id] = {
          can_transition_to_implemented: false,
          validation_errors: [],
          linked_evidence_count: 0,
          has_sufficient_implementation_details: !!(item.implementation_description && item.implementation_description.length >= 15),
          imr_item_id: item.id,
          current_status: item.pearo_status,
        }
      }
    }
    setValidationStatuses(statuses)
  }

  const startItem = (page - 1) * PAGE_SIZE + 1
  const endItem = page * PAGE_SIZE

  if (loading) {
    return <div className="text-center py-8">{t("common.loading")}</div>
  }

  if (error) {
    return <div className="text-red-600 py-4">{t("common.info")}: {error}</div>
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        {t("implementationPlan.table.noData")}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <th className="p-3">{t("implementationPlan.table.code")}</th>
            <th className="p-3">{t("implementationPlan.table.measure")}</th>
            <th className="p-3">{t("implementationPlan.table.status")}</th>
            <th className="p-3">{t("implementationPlan.table.priority")}</th>
            <th className="p-3">{t("implementationPlan.table.dueDate")}</th>
            <th className="p-3">{t("implementationPlan.table.responsible")}</th>
            <th className="p-3 text-center">{t("implementationPlan.table.validation")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((item) => {
            const validation = validationStatuses[item.id]
            const canTransition = validation?.can_transition_to_implemented ?? false
            
            return (
              <tr 
                key={item.id} 
                onClick={() => onEditItem?.(item)}
                className="hover:bg-slate-100 cursor-pointer transition-colors border-b border-slate-100"
              >
                <td className="p-3">
                  <span className="font-bold text-blue-800 text-sm">
                    {item.measure?.code || "N/A"}
                  </span>
                </td>
                <td className="p-3">
                  <div className="max-w-xs">
                    <span className="font-medium text-slate-900 text-sm truncate block" title={item.measure?.name}>
                      {item.measure?.name || "N/A"}
                    </span>
                    {item.implementation_description && (
                      <span className="text-xs text-slate-500 truncate block mt-0.5">
                        {item.implementation_description.substring(0, 50)}...
                      </span>
                    )}
                  </div>
                </td>
                <td className="p-3">
                  <ImrStatusBadge status={item.pearo_status} size="sm" />
                </td>
                <td className="p-3">
                  <ImrPriorityBadge priority={item.priority} />
                </td>
                <td className="p-3">
                  <span className={`text-sm ${isOverdue(item) ? "text-red-600 font-medium" : "text-slate-600"}`}>
                    {item.due_date ? formatDate(item.due_date) : "Määramata"}
                  </span>
                </td>
                <td className="p-3">
                  <span className="text-sm text-slate-600">
                    {item.responsible_user_id || t("implementationPlan.table.unassigned")}
                  </span>
                </td>
                <td className="p-3 text-center">
                  {item.pearo_status !== "R" && (
                    <ImrValidationIndicator 
                      canTransition={canTransition}
                      hasEvidence={(validation?.linked_evidence_count ?? 0) > 0}
                      hasSufficientDetails={validation?.has_sufficient_implementation_details ?? false}
                    />
                  )}
                  {item.pearo_status === "R" && (
                    <span className="text-emerald-600">✓</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-slate-300 bg-slate-100">
        <div className="text-sm font-bold text-slate-700">
          {startItem} - {endItem}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm font-bold border-2 border-slate-400 rounded-lg bg-white text-slate-700 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← {t("implementationPlan.pagination.previous")}
          </button>
          <span className="px-4 py-2 text-sm font-bold text-slate-800 bg-slate-200 rounded-lg border-2 border-slate-300">
            {t("implementationPlan.pagination.page")} {page}
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore}
            className="px-4 py-2 text-sm font-bold border-2 border-slate-400 rounded-lg bg-white text-slate-700 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {t("implementationPlan.pagination.next")} →
          </button>
        </div>
      </div>
    </div>
  )
}

function isOverdue(item: ImrItem): boolean {
  if (!item.due_date || item.pearo_status === "R" || item.pearo_status === "A") return false
  const today = new Date().toISOString().split("T")[0]
  return item.due_date < today
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("et-EE", { year: "numeric", month: "short", day: "numeric" })
}