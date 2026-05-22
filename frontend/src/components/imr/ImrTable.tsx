import { useState, useEffect, useMemo } from "react"
import { ImrItem, ImrValidationStatus } from "@/lib/imr-types"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { ImrStatusBadge, ImrPriorityBadge, ImrValidationIndicator } from "./ImrStatusBadge"

type SortField = "code" | "status" | "priority" | "dueDate" | "profile" | "responsible" | "todo" | "cost"
type SortOrder = "asc" | "desc"

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
  const { loading, error, fetchImrItems, fetchUsers } = useImrApi()
  const [items, setItems] = useState<ImrItem[]>([])
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ImrValidationStatus>>({})
  const [users, setUsers] = useState<Record<string, string>>({})
  const [sortField, setSortField] = useState<SortField>("dueDate")
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc")
  
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
    
    // Fetch user names
    const userList = await fetchUsers()
    const userMap: Record<string, string> = {}
    userList.forEach((u: any) => { userMap[u.id] = u.full_name })
    setUsers(userMap)
    
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

  const sortedItems = useMemo(() => {
    const sorted = [...items].sort((a, b) => {
      let cmp = 0
      switch (sortField) {
        case "code":
          cmp = (a.measure?.code || "").localeCompare(b.measure?.code || "")
          break
        case "status":
          cmp = a.pearo_status.localeCompare(b.pearo_status)
          break
        case "priority":
          const priorityOrder = { P1: 1, P2: 2, P3: 3 }
          cmp = (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2)
          break
        case "dueDate":
          cmp = (a.due_date || "").localeCompare(b.due_date || "")
          break
        case "profile":
          cmp = (a.requirement_profile || "").localeCompare(b.requirement_profile || "")
          break
        case "responsible":
          cmp = (users[a.responsible_user_id] || "").localeCompare(users[b.responsible_user_id] || "")
          break
        case "todo":
          cmp = (a.todo_description || "").localeCompare(b.todo_description || "")
          break
        case "cost":
          cmp = (a.cost_eur || 0) - (b.cost_eur || 0)
          break
      }
      return sortOrder === "asc" ? cmp : -cmp
    })
    return sorted
  }, [items, sortField, sortOrder, users])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortOrder("asc")
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => (
    <span className="ml-1 text-xs">
      {sortField === field ? (sortOrder === "asc" ? "↑" : "↓") : "↕"}
    </span>
  )

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
    <div className="overflow-x-auto bg-card">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="bg-slate-100 dark:bg-slate-800 border-b border-border font-semibold text-muted-foreground uppercase tracking-wider">
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-20"
              onClick={() => handleSort("code")}
            >
              {t("implementationPlan.table.code")}<SortIcon field="code" />
            </th>
            <th className="py-2 px-2">{t("implementationPlan.table.measure")}</th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-24"
              onClick={() => handleSort("status")}
            >
              {t("implementationPlan.table.status")}<SortIcon field="status" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-20"
              onClick={() => handleSort("priority")}
            >
              {t("implementationPlan.table.priority")}<SortIcon field="priority" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-24"
              onClick={() => handleSort("dueDate")}
            >
              {t("implementationPlan.table.dueDate")}<SortIcon field="dueDate" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none"
              onClick={() => handleSort("responsible")}
            >
              {t("implementationPlan.table.responsible")}<SortIcon field="responsible" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-20"
              onClick={() => handleSort("profile")}
            >
              {t("implementationPlan.table.profile")}<SortIcon field="profile" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none"
              onClick={() => handleSort("todo")}
            >
              {t("implementationPlan.modal.todoDescription")}<SortIcon field="todo" />
            </th>
            <th 
              className="py-2 px-2 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 select-none w-20 text-right"
              onClick={() => handleSort("cost")}
            >
              {t("implementationPlan.modal.costEur")}<SortIcon field="cost" />
            </th>
            <th className="py-2 px-2 text-center w-16">{t("implementationPlan.table.validation")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
          {sortedItems.map((item) => {
            const validation = validationStatuses[item.id]
            const canTransition = validation?.can_transition_to_implemented ?? false
            
            return (
              <tr 
                key={item.id} 
                onClick={() => onEditItem?.(item)}
                className="hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors border-b border-slate-200 dark:border-slate-700"
              >
                <td className="py-2 px-2">
                  <span className="font-bold text-blue-600 dark:text-blue-300">
                    {item.measure?.code || "N/A"}
                  </span>
                </td>
                <td className="py-2 px-2">
                  <span className="font-medium text-foreground truncate block" title={item.measure?.name}>
                    {item.measure?.name || "N/A"}
                  </span>
                </td>
                <td className="py-2 px-2">
                  <ImrStatusBadge status={item.pearo_status} size="sm" />
                </td>
                <td className="py-2 px-2">
                  <ImrPriorityBadge priority={item.priority} />
                </td>
                <td className="py-2 px-2">
                  <span className={`${isOverdue(item) ? "text-red-600 font-medium" : "text-muted-foreground"}`}>
                    {item.due_date ? formatDate(item.due_date) : "—"}
                  </span>
                </td>
                <td className="py-2 px-2">
                  <span className="text-muted-foreground truncate block" title={item.responsible_user_id ? users[item.responsible_user_id] : undefined}>
                    {item.responsible_user_id ? (users[item.responsible_user_id] || "—") : t("implementationPlan.table.unassigned")}
                  </span>
                </td>
                <td className="py-2 px-2">
                  {item.requirement_profile ? (
                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                      item.requirement_profile === "PÕHIMEEDE" 
                        ? "bg-emerald-100 text-emerald-800" 
                        : "bg-amber-100 text-amber-800"
                    }`}>
                      {item.requirement_profile}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </td>
                <td className="py-2 px-2">
                  {item.todo_description ? (
                    <span className="text-muted-foreground truncate block max-w-[120px]" title={item.todo_description}>
                      {item.todo_description.substring(0, 20)}...
                    </span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="py-2 px-2 text-right">
                  {item.cost_eur !== undefined && item.cost_eur !== null ? (
                    <span className="text-muted-foreground">{item.cost_eur.toFixed(0)}</span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="py-2 px-2 text-center">
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
      <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted">
        <div className="text-sm font-bold text-foreground">
          {startItem} - {endItem}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm font-bold border-2 border-border rounded-lg bg-card text-foreground hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← {t("implementationPlan.pagination.previous")}
          </button>
          <span className="px-4 py-2 text-sm font-bold text-foreground bg-muted rounded-lg border-2 border-border">
            {t("implementationPlan.pagination.page")} {page}
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore}
            className="px-4 py-2 text-sm font-bold border-2 border-border rounded-lg bg-card text-foreground hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
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