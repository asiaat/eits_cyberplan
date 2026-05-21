import { useState, useEffect } from "react"
import { ImrItem, ImrItemUpdate, IMR_STATUS_OPTIONS, IMR_PRIORITY_OPTIONS, ImrValidationStatus } from "@/lib/imr-types"
import { useImrApi } from "@/lib/use-imr-api"
import { useTranslation } from "@/lib/i18n"
import { apiClient } from "@/lib/api-client"

interface ImrItemModalProps {
  item: ImrItem | null
  isOpen: boolean
  onClose: () => void
  onSave: (item: ImrItem) => void
}

interface EvidenceItem {
  id: string
  title: string
  evidence_type: string
}

interface UserOption {
  id: string
  full_name: string
  email: string
  department: string | null
}

export function ImrItemModal({ item, isOpen, onClose, onSave }: ImrItemModalProps) {
  const { t } = useTranslation()
  const { updateImrItem, getImrValidationStatus, linkEvidenceToImr, loading, fetchUsers } = useImrApi()
  
  const [formData, setFormData] = useState<ImrItemUpdate>({})
  const [validationStatus, setValidationStatus] = useState<ImrValidationStatus | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [availableEvidences, setAvailableEvidences] = useState<EvidenceItem[]>([])
  const [showEvidenceSelector, setShowEvidenceSelector] = useState(false)
  const [linkingLoading, setLinkingLoading] = useState(false)
  const [availableUsers, setAvailableUsers] = useState<UserOption[]>([])

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

  const loadAvailableUsers = async () => {
    try {
      const users = await fetchUsers()
      setAvailableUsers(users)
    } catch (err) {
      console.error("Failed to load users", err)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadAvailableUsers()
    }
  }, [isOpen])

  const loadAvailableEvidences = async () => {
    try {
      const response = await apiClient.get("/evidences")
      setAvailableEvidences(response.data || [])
    } catch (err) {
      console.error("Failed to load evidences", err)
    }
  }

  const handleLinkEvidence = async (evidenceId: string) => {
    if (!item) return
    setLinkingLoading(true)
    try {
      await linkEvidenceToImr(item.id, evidenceId)
      await loadValidationStatus()
      setShowEvidenceSelector(false)
    } catch (err) {
      console.error("Failed to link evidence", err)
    } finally {
      setLinkingLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!item) return
    
    setSaveError(null)
    
    if (formData.pearo_status === "R" && item.pearo_status !== "R") {
      const freshValidation = await getImrValidationStatus(item.id)
      if (freshValidation && !freshValidation.can_transition_to_implemented) {
        const errors = freshValidation.validation_errors.join("; ")
        setSaveError(errors)
        setValidationStatus(freshValidation)
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
    
    if (newStatus === "R" && item && item.pearo_status !== "R") {
      if (validationStatus && !validationStatus.can_transition_to_implemented) {
        setSaveError(t("implementationPlan.validation.markImplementedWarning"))
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
              {t("implementationPlan.modal.title")}: <span className="text-blue-800">{item.measure?.code}</span>
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
                <h4 className="font-semibold text-amber-800">{t("implementationPlan.validation.missingDescription")}</h4>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Status and Priority Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
              <label className="block text-sm font-bold text-slate-800 mb-2">
                {t("implementationPlan.table.status")}
              </label>
              <select
                value={formData.pearo_status || ""}
                onChange={(e) => handleStatusChange(e.target.value)}
                className="w-full border border-slate-400 bg-white rounded-lg p-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {IMR_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value} className="text-slate-900">
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
              <label className="block text-sm font-bold text-slate-800 mb-2">
                {t("implementationPlan.table.priority")}
              </label>
              <select
                value={formData.priority || ""}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                className="w-full border border-slate-400 bg-white rounded-lg p-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {IMR_PRIORITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value} className="text-slate-900">
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Due Date */}
          <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
            <label className="block text-sm font-bold text-slate-800 mb-2">
              {t("implementationPlan.table.dueDate")}
            </label>
            <input
              type="date"
              value={formData.due_date || ""}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              className="w-full border border-slate-400 bg-white rounded-lg p-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Responsible Person */}
          <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
            <label className="block text-sm font-bold text-slate-800 mb-2">
              {t("implementationPlan.table.responsible")}
            </label>
            <select
              value={formData.responsible_user_id || ""}
              onChange={(e) => setFormData({ ...formData, responsible_user_id: e.target.value || undefined })}
              className="w-full border border-slate-400 bg-white rounded-lg p-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="" className="text-slate-900">Vali vastutaja...</option>
              {availableUsers.map((user) => (
                <option key={user.id} value={user.id} className="text-slate-900">
                  {user.full_name} {user.department ? `(${user.department})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Implementation Description */}
          <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
            <label className="block text-sm font-bold text-slate-800 mb-2">
              {t("implementationPlan.modal.implementationDescription")} {formData.pearo_status === "R" && <span className="text-red-500">*</span>}
            </label>
            <textarea
              value={formData.implementation_description || ""}
              onChange={(e) => setFormData({ ...formData, implementation_description: e.target.value })}
              rows={5}
              placeholder="Kirjelda tegevused, mis tõendavad meetme toimimist..."
              className="w-full border border-slate-400 bg-white rounded-lg p-3 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="mt-1 text-xs text-slate-600">
              {formData.implementation_description?.length || 0}/15 {t("implementationPlan.modal.charactersMin")}
            </p>
          </div>

          {/* Verification Method */}
          <div className="bg-slate-100 p-4 rounded-lg border border-slate-300">
            <label className="block text-sm font-bold text-slate-800 mb-2">
              {t("implementationPlan.modal.verificationMethod")}
            </label>
            <input
              type="text"
              value={formData.verification_method || ""}
              onChange={(e) => setFormData({ ...formData, verification_method: e.target.value })}
              placeholder="nt Kontrollitud dokumentatsioon, Test, Inspektsioon"
              className="w-full border border-slate-400 bg-white rounded-lg p-2.5 text-sm text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Evidence Indicator */}
          <div className={`p-4 rounded-lg border ${
            validationStatus?.linked_evidence_count && validationStatus.linked_evidence_count > 0 
              ? "bg-emerald-100 border-emerald-300" 
              : "bg-slate-100 border-slate-300"
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{validationStatus?.linked_evidence_count && validationStatus.linked_evidence_count > 0 ? "✓" : "○"}</span>
                <span className="text-sm font-bold text-slate-800">
                  {t("implementationPlan.modal.evidenceCount")}: {validationStatus?.linked_evidence_count || 0}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowEvidenceSelector(true)
                  loadAvailableEvidences()
                }}
                className="text-sm font-bold text-indigo-600 hover:text-indigo-900 bg-white px-3 py-1 rounded border border-indigo-300"
              >
                {t("evidences.linkExisting") || "Link Evidence"}
              </button>
            </div>
          </div>
        </form>

        {/* Evidence Selector Modal */}
        {showEvidenceSelector && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold">{t("evidences.selectEvidence")}</h3>
                <button onClick={() => setShowEvidenceSelector(false)} className="text-slate-400 hover:text-slate-600 text-2xl">×</button>
              </div>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {availableEvidences.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">{t("evidences.noAvailable") || "No evidence available"}</p>
                ) : (
                  availableEvidences.map((evidence) => (
                    <div
                      key={evidence.id}
                      onClick={() => handleLinkEvidence(evidence.id)}
                      className="p-3 border border-slate-300 rounded-lg hover:bg-slate-100 cursor-pointer bg-slate-50"
                    >
                      <span className="text-sm font-medium">{evidence.title}</span>
                      <span className="text-xs text-slate-500 ml-2">{evidence.evidence_type}</span>
                    </div>
                  ))
                )}
              </div>
              {linkingLoading && (
                <div className="text-center py-4 text-sm text-slate-500">
                  {t("common.loading")}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-slate-200 p-4 bg-slate-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100"
          >
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? t("implementationPlan.modal.saving") : t("common.save")}
          </button>
        </div>
      </div>
    </div>
  )
}