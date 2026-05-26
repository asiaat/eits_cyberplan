import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Shield, FileIcon, Link2, Unlink, CheckCircle, AlertTriangle } from "lucide-react"
import { ErrorDialog } from "@/components/ui/error-dialog"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface LinkedEvidence {
  id: string
  title: string
  evidence_type: string
  file_hash: string | null
}

interface ProtectionModeSelection {
  id: string
  tenant_id: string
  catalog_version_id: string | null
  catalog_version_name: string | null
  security_approach: string
  approach_display: string
  evidence_id: string | null
  evidence: LinkedEvidence | null
  approved_by: string | null
  approved_by_name: string | null
  approved_at: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

interface ApproachItem {
  code: string
}

interface EvidenceItem {
  id: string
  title: string
  evidence_type: string
  file_hash: string | null
}

const approachColors: Record<string, string> = {
  BASIC: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200",
  CORE: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200",
}

export default function ProtectionModePage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const selectedOrgIdRef = useRef(selectedOrgId)

  const [selections, setSelections] = useState<ProtectionModeSelection[]>([])
  const [approachCodes, setApproachCodes] = useState<{ approaches: ApproachItem[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorDialog, setErrorDialog] = useState<{ open: boolean; message: string }>({ open: false, message: "" })
  const [showEvidenceDialog, setShowEvidenceDialog] = useState(false)
  const [selectedSelection, setSelectedSelection] = useState<ProtectionModeSelection | null>(null)
  const [availableEvidences, setAvailableEvidences] = useState<EvidenceItem[]>([])
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null)
  const [showChangeConfirmDialog, setShowChangeConfirmDialog] = useState(false)
  const [pendingApproach, setPendingApproach] = useState<string | null>(null)
  const [imrPreviewStats, setImrPreviewStats] = useState<{ approach: string; measures_count: number } | null>(null)
  const [changingMode, setChangingMode] = useState(false)

  useEffect(() => { selectedOrgIdRef.current = selectedOrgId }, [selectedOrgId])

  useEffect(() => {
    fetchSelections()
    fetchApproachCodes()
  }, [selectedOrgId])

  const fetchSelections = async () => {
    try {
      setLoading(true)
      setError(null)
      const timestamp = Date.now()
      const response = await apiClient.get(`/protection-mode/?_=${timestamp}`)
      const data = response.data || []
      setSelections(data)
    } catch (err: any) {
      console.error("Failed to fetch protection mode selections:", err)
      setError(err.response?.data?.detail || "Failed to load protection modes")
    } finally {
      setLoading(false)
    }
  }

  const handleSelectApproach = async (approachCode: string) => {
    setPendingApproach(approachCode)
    try {
      const response = await apiClient.get(`/protection-mode/imr-preview?approach=${approachCode}`)
      setImrPreviewStats(response.data)
    } catch {
      setImrPreviewStats({ approach: approachCode, measures_count: 0 })
    }
    setShowChangeConfirmDialog(true)
  }

  const handleConfirmModeChange = async () => {
    if (!pendingApproach) return
    setChangingMode(true)
    try {
      await apiClient.post("/protection-mode/", {
        security_approach: pendingApproach,
      })

      await apiClient.post("/protection-mode/regenerate-imr")

      setShowChangeConfirmDialog(false)
      setPendingApproach(null)
      setTimeout(() => {
        fetchSelections()
      }, 100)
    } catch (err: any) {
      console.error("Failed to change protection mode:", err)
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to change protection mode" })
    } finally {
      setChangingMode(false)
    }
  }

  const handleCancelModeChange = () => {
    setShowChangeConfirmDialog(false)
    setPendingApproach(null)
    setImrPreviewStats(null)
  }

  const fetchApproachCodes = async () => {
    try {
      const response = await apiClient.get("/protection-mode/approaches/list")
      setApproachCodes(response.data)
    } catch (err) {
      console.error("Failed to fetch approach codes:", err)
    }
  }

  const handleLinkEvidence = async (selectionId: string, evidenceId: string) => {
    try {
      const response = await apiClient.post(`/protection-mode/${selectionId}/link-evidence`, {
        evidence_id: evidenceId,
      })
      setSelections(selections.map(s => s.id === selectionId ? response.data : s))
      setShowEvidenceDialog(false)
      setSelectedSelection(null)
    } catch (err: any) {
      console.error("Failed to link evidence:", err)
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to link evidence" })
    }
  }

  const handleUnlinkEvidence = async (selectionId: string) => {
    try {
      const response = await apiClient.delete(`/protection-mode/${selectionId}/unlink-evidence`)
      setSelections(selections.map(s => s.id === selectionId ? response.data : s))
    } catch (err: any) {
      console.error("Failed to unlink evidence:", err)
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to unlink evidence" })
    }
  }

  const handleDeactivateClick = (selectionId: string) => {
    setDeactivatingId(selectionId)
  }

  const handleDeactivateConfirm = async () => {
    if (!deactivatingId) return
    try {
      await apiClient.patch(`/protection-mode/${deactivatingId}`, { is_active: false })
      setDeactivatingId(null)
      fetchSelections()
    } catch (err: any) {
      console.error("Failed to deactivate:", err)
      setErrorDialog({ open: true, message: err.response?.data?.detail || "Failed to deactivate" })
    }
  }

  const handleDeactivateCancel = () => {
    setDeactivatingId(null)
  }

  const openEvidenceDialog = async (selection: ProtectionModeSelection) => {
    setSelectedSelection(selection)
    try {
      const response = await apiClient.get("/evidences")
      setAvailableEvidences(response.data || [])
      setShowEvidenceDialog(true)
    } catch (err) {
      console.error("Failed to fetch evidences:", err)
    }
  }

  const approachCodeToKey = (code: string | null | undefined): string => {
    if (!code) return ""
    const map: Record<string, string> = {
      BASIC: "basic",
      STANDARD: "standard",
      CORE: "core",
    }
    return map[code] || code.toLowerCase()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">{t("common.loading")}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">{t("protectionmode.title")}</h1>
            <p className="text-muted-foreground mt-1">{t("protectionmode.description")}</p>
          </div>
        </div>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {approachCodes && approachCodes.approaches && (
        <div className="grid gap-6 md:grid-cols-3">
          {approachCodes.approaches.map((approach) => {
            const approachKey = approachCodeToKey(approach.code)
            const selection = selections.find(s => s.security_approach === approach.code)
            const isActive = selection?.is_active
            const hasEvidence = selection?.evidence_id

            return (
              <Card
                key={approach.code}
                className={`relative ${isActive ? "ring-2 ring-primary" : ""}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <Badge variant="outline" className={approachColors[approach.code]}>
                        {t(`protectionmode.approaches.${approachKey}.name`)}
                      </Badge>
                      <CardTitle className="mt-2 text-xl">
                        {t(`protectionmode.approaches.${approachKey}.subtitle`)}
                      </CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm">{t(`protectionmode.approaches.${approachKey}.description`)}</p>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">{t("protectionmode.whenToUse")}</h4>
                    <p className="text-xs text-muted-foreground bg-muted p-2 rounded">
                      {t(`protectionmode.approaches.${approachKey}.when`)}
                    </p>
                  </div>

                  <div className="space-y-3 pt-2 border-t">
                    <div className="flex items-center gap-2">
                      {isActive && (
                        <Badge variant="default" className="bg-green-600">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          {t("protectionmode.isActive")}
                        </Badge>
                      )}
                    </div>

                    {isActive ? (
                      <>
                        {hasEvidence ? (
                          <div className="flex items-center justify-between bg-muted p-3 rounded-lg">
                            <div className="flex items-center gap-2">
                              <FileIcon className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{selection.evidence?.title}</span>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUnlinkEvidence(selection.id)}
                            >
                              <Unlink className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full"
                            onClick={() => openEvidenceDialog(selection)}
                          >
                            <Link2 className="h-4 w-4 mr-2" />
                            {t("protectionmode.linkEvidence")}
                          </Button>
                        )}

                        <Button
                          variant="destructive"
                          size="sm"
                          className="w-full"
                          onClick={() => handleDeactivateClick(selection.id)}
                        >
                          {t("protectionmode.deactivate")}
                        </Button>
                      </>
                    ) : selections.some(s => s.is_active) ? (
                      <div />
                    ) : (
                      <Button
                        variant="default"
                        className="w-full"
                        onClick={() => handleSelectApproach(approach.code)}
                      >
                        {t("protectionmode.selectApproach")}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {selections.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">{t("protectionmode.activeMode")}</h3>
          <div className="grid gap-4">
            {selections.filter(s => s.is_active).map(selection => {
              const approachKey = approachCodeToKey(selection.security_approach)
              return (
                <Card key={selection.id} className="bg-primary/5">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Shield className="h-5 w-5 text-primary" />
                          <span className="font-medium">
                            {t(`protectionmode.approaches.${approachKey}.name`)}
                          </span>
                          {selection.catalog_version_name && (
                            <Badge variant="outline">{selection.catalog_version_name}</Badge>
                          )}
                        </div>
                        {selection.notes && (
                          <p className="text-sm text-muted-foreground">{selection.notes}</p>
                        )}
                        {selection.approved_by_name && (
                          <p className="text-xs text-muted-foreground">
                            {t("protectionmode.approvedBy")}: {selection.approved_by_name}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      <Dialog open={showEvidenceDialog} onOpenChange={(open) => {
        setShowEvidenceDialog(open)
        if (!open) {
          setSelectedSelection(null)
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("protectionmode.selectEvidence")}</DialogTitle>
            <DialogDescription>
              {t("protectionmode.description")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {availableEvidences.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                {t("evidences.noData")}
              </p>
            ) : (
              availableEvidences.map((evidence) => (
                <div
                  key={evidence.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted cursor-pointer"
                  onClick={() => selectedSelection && handleLinkEvidence(selectedSelection.id, evidence.id)}
                >
                  <div className="flex items-center gap-3">
                    <FileIcon className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{evidence.title}</p>
                      <p className="text-xs text-muted-foreground">{evidence.evidence_type}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEvidenceDialog(false)}>
              {t("common.cancel")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deactivatingId !== null} onOpenChange={(open) => {
        if (!open) {
          handleDeactivateCancel()
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              {t("protectionmode.confirmDeactivateTitle")}
            </DialogTitle>
            <DialogDescription className="space-y-3 pt-2">
              <p>{t("protectionmode.confirmDeactivateDesc")}</p>
              <p className="font-medium text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded border border-yellow-200 dark:border-yellow-800">
                {t("protectionmode.confirmDeactivateWarning")}
              </p>
              <p className="font-semibold text-foreground">{t("protectionmode.confirmDeactivateAssurance")}</p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={handleDeactivateCancel}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={handleDeactivateConfirm}>
              {t("protectionmode.confirmDeactivateButton")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showChangeConfirmDialog} onOpenChange={(open) => {
        if (!open) {
          handleCancelModeChange()
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-amber-500 mr-2" />
              {t("protectionmode.confirmModeChangeTitle") || "Kaitse režiimi muutmine"}
            </DialogTitle>
            <DialogDescription className="space-y-3 pt-2">
              <p>{t("protectionmode.confirmModeChangeDesc") || "Kaitse režiimi muutmine kustutab kõik olemasolevad IMR kirjed ja loob uued vastavalt uuele režiimile."}</p>
              {imrPreviewStats && (
                <p className="font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 p-3 rounded border border-blue-200 dark:border-blue-800">
                  {t("protectionmode.imrWillBeGenerated") || "Luuakse"} {imrPreviewStats.measures_count} {t("protectionmode.measures") || "meedet"} ({t(`protectionmode.approaches.${approachCodeToKey(pendingApproach)}.name`)})
                </p>
              )}
              <p className="font-semibold text-destructive">{t("protectionmode.confirmModeChangeWarning") || "See toiming ei ole tagasivõetav!"}</p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={handleCancelModeChange} disabled={changingMode}>
              {t("common.cancel")}
            </Button>
            <Button variant="default" onClick={handleConfirmModeChange} disabled={changingMode}>
              {changingMode ? (t("common.loading") || "Loading...") : (t("protectionmode.confirmModeChangeButton") || " Kinnita ja jätka ")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ErrorDialog
        open={errorDialog.open}
        onOpenChange={(open) => setErrorDialog(prev => ({ ...prev, open }))}
        title="Error"
        message={errorDialog.message}
      />
    </div>
  )
}