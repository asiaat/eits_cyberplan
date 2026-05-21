import { useState, useEffect } from "react"
import { ImrItem, ImrValidationStatus } from "@/lib/imr-types"
import { useImrApi } from "@/lib/use-imr-api"
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
  const { loading, error, fetchImrItems } = useImrApi()
  const [items, setItems] = useState<ImrItem[]>([])
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ImrValidationStatus>>({})

  useEffect(() => {
    loadItems()
  }, [filters])

  const loadItems = async () => {
    const fetchedItems = await fetchImrItems(filters)
    setItems(fetchedItems)
    
    // Load validation status for each item
    const statuses: Record<string, ImrValidationStatus> = {}
    for (const item of fetchedItems) {
      if (item.pearo_status !== "R") {
        // We would fetch validation status here, but for simplicity we'll just mark it
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

  if (loading) {
    return <div className="text-center py-8">Laadimine...</div>
  }

  if (error) {
    return <div className="text-red-600 py-4">Viga: {error}</div>
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        IMR itemsid ei leitud
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <th className="p-3">Kood</th>
            <th className="p-3">Meede</th>
            <th className="p-3">Olek</th>
            <th className="p-3">Prioriteet</th>
            <th className="p-3">Tähtaeg</th>
            <th className="p-3">Vastutaja</th>
            <th className="p-3 text-center">Valideerimine</th>
            <th className="p-3 text-right">Tegevus</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((item) => {
            const validation = validationStatuses[item.id]
            const canTransition = validation?.can_transition_to_implemented ?? false
            
            return (
              <tr 
                key={item.id} 
                className="hover:bg-slate-50/50 transition-colors border-b border-slate-100"
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
                    {item.responsible_user_id || "Määramata"}
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
                <td className="p-3 text-right">
                  <button
                    onClick={() => onEditItem?.(item)}
                    className="text-xs text-indigo-600 hover:text-indigo-900 font-medium hover:underline"
                  >
                    Täida meedet
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
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