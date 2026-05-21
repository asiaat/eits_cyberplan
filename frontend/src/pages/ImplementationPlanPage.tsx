import { useState } from "react"
import { ImrTable } from "@/components/imr/ImrTable"
import { ImrItemModal } from "@/components/imr/ImrItemModal"
import { ImrDashboardStats } from "@/components/imr/ImrDashboardStats"
import { ImrItem, IMR_STATUS_OPTIONS } from "@/lib/imr-types"

export default function ImplementationPlanPage() {
  const [selectedItem, setSelectedItem] = useState<ImrItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
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

  const handleSaveItem = (updatedItem: ImrItem) => {
    // Refresh the table by closing modal - parent will re-fetch
    console.log("Item saved:", updatedItem.id)
  }

  return (
    <div className="min-h-screen bg-slate-50 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Infoturbe meetmete rakenduskava (IMR)
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Skoobi modelleerimisel loodud meetmete rakenduse jälgimine
            </p>
          </div>
        </div>

        {/* Dashboard Statistics */}
        <ImrDashboardStats />

        {/* Filter Bar */}
        <div className="mb-4 bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Oleku filter
              </label>
              <select
                value={filter.pearo_status || ""}
                onChange={(e) => setFilter({ ...filter, pearo_status: e.target.value || undefined })}
                className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Kõik olekud</option>
                {IMR_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} - {option.label.split(" - ")[1]}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Üleatekohad
              </label>
              <label className="inline-flex items-center">
                <input
                  type="checkbox"
                  checked={filter.overdue_only || false}
                  onChange={(e) => setFilter({ ...filter, overdue_only: e.target.checked || undefined })}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-slate-600">Näita ainult ületähtajaga</span>
              </label>
            </div>

            {(filter.pearo_status || filter.overdue_only) && (
              <button
                onClick={() => setFilter({})}
                className="text-sm text-indigo-600 hover:text-indigo-900 underline"
              >
                Eemalda filtrid
              </button>
            )}
          </div>
        </div>

        {/* IMR Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <ImrTable onEditItem={handleEditItem} filters={filter} />
        </div>

        {/* IMR Item Modal */}
        <ImrItemModal
          item={selectedItem}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSave={handleSaveItem}
        />
      </div>
    </div>
  )
}