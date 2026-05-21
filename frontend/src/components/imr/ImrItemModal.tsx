import { useState, useEffect } from "react"
import { ImrItem, ImrItemUpdate, IMR_STATUS_OPTIONS, IMR_PRIORITY_OPTIONS, ImrValidationStatus } from "@/lib/imr-types"
import { useImrApi } from "@/lib/use-imr-api"

interface ImrItemModalProps {
  item: ImrItem | null
  isOpen: boolean
  onClose: () => void
  onSave: (item: ImrItem) => void
}

export function ImrItemModal({ item, isOpen, onClose, onSave }: ImrItemModalProps) {
  const { updateImrItem, getImrValidationStatus, loading } = useImrApi()
  
  const [formData, setFormData] = useState<ImrItemUpdate>({})
  const [validationStatus, setValidationStatus] = useState<ImrValidationStatus | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    if (item) {
      setFormData({
        pearo_status: item.pearo_status,
        implementation_description: item.implementation_description || "",
        priority: item.priority,
        due_date: item.due_date,
        responsible_user_id: item.responsible_user_id,
        verification_method: item.verification_method || "",
      })
      
      // Get validation status if not already implemented
      if (item.pearo_status !== "R") {
        loadValidationStatus()
      }
    }
  }, [item])

  const loadValidationStatus = async () => {
    if (!item) return
    const status = await getImrValidationStatus(item.id)
    setValidationStatus(status)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!item) return
    
    setSaveError(null)
    
    // If trying to save as "R" (Implemented), validate first
    if (formData.pearo_status === "R") {
      const isValid = validationStatus?.can_transition_to_implemented ?? false
      if (!isValid) {
        const errors = validationStatus?.validation_errors?.join("; ") || "Valideerimise viga"
        setSaveError(errors)
        return
      }
    }
    
    const updatedItem = await updateImrItem(item.id, formData)
    if (updatedItem) {
      onSave(updatedItem)
      onClose()
    }
  }

  const handleStatusChange = (newStatus: string) => {
    setFormData({ ...formData, pearo_status: newStatus as any })
    
    // Check if transitioning to R
    if (newStatus === "R" && item && item.pearo_status !== "R") {
      // Show warning if not valid
      if (validationStatus && !validationStatus.can_transition_to_implemented) {
        setSaveError("Märgi 'Rakendatud' saab ainult siis, kui on olemas piisav teostuskirjeldus (min 15 tähemärki) ja vähemalt üks asitõend.")
      }
    }
  }

  if (!isOpen || !item) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-start border-b border-slate-200 p-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Meetme andmete täitmine: <span className="text-blue-800">{item.measure?.code}</span>
            </h2>
            <p className="text-sm text-slate-500 mt-1">{item.measure?.name}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Validation Warning Banner */}
        {validationStatus && !validationStatus.can_transition_to_implemented && formData.pearo_status !== "R" && (
          <div className="mx-6 mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-amber-600 text-xl">⚠</span>
              <div>
                <h4 className="font-semibold text-amber-800">Valideerimise viga</h4>
                <ul className="mt-2 text-sm text-amber-700 space-y-1">
                  {validationStatus.validation_errors.map((error, i) => (
                    <li key={i}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {saveError && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {saveError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Status and Priority Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                  Olek
                </label>
                <select
                  value={formData.pearo_status || ""}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {IMR_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                  Prioriteet
                </label>
                <select
                  value={formData.priority || ""}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {IMR_PRIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Due Date */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                Tähtaeg
              </label>
              <input
                type="date"
                value={formData.due_date || ""}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Implementation Description */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                Teostuskirjeldus {formData.pearo_status === "R" && <span className="text-red-500">*</span>}
              </label>
              <textarea
                value={formData.implementation_description || ""}
                onChange={(e) => setFormData({ ...formData, implementation_description: e.target.value })}
                rows={4}
                placeholder="Kirjelda tegevused, mis tõendavad meetme toimimist..."
                className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="mt-1 text-xs text-slate-500">
                {formData.implementation_description?.length || 0}/15 tähemärki minimaalselt
              </p>
            </div>

            {/* Verification Method */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                Verifitseerimise meetod
              </label>
              <input
                type="text"
                value={formData.verification_method || ""}
                onChange={(e) => setFormData({ ...formData, verification_method: e.target.value })}
                placeholder="nt Kontrollitud dokumentatsioon, Test, Inspektsioon"
                className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Evidence Indicator */}
            {validationStatus && (
              <div className={`p-4 rounded-lg border ${
                validationStatus.linked_evidence_count > 0 
                  ? "bg-emerald-50 border-emerald-200" 
                  : "bg-slate-50 border-slate-200"
              }`}>
                <div className="flex items-center gap-2">
                  <span>{validationStatus.linked_evidence_count > 0 ? "✓" : "○"}</span>
                  <span className="text-sm font-medium">
                    Seotud asitõendeid: {validationStatus.linked_evidence_count}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 border-t border-slate-100 pt-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200"
            >
              Tühista
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? "Salvestamine..." : "Salvesta"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}