import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Shield, FileIcon, Link2, Unlink, CheckCircle } from "lucide-react"
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

interface TurbeviisSelection {
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

const approachColors: Record<string, string> = {
  BASIC: "bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200",
  STANDARD: "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-200",
  CORE: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-200",
}

export default function TurbeviisPage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const selectedOrgIdRef = useRef(selectedOrgId)

  const [selections, setSelections] = useState<TurbeviisSelection[]>([])
  const [approachCodes, setApproachCodes] = useState<{ approaches: ApproachItem[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEvidenceDialog, setShowEvidenceDialog] = useState(false)
  const [selectedSelection, setSelectedSelection] = useState<TurbeviisSelection | null>(null)
  const [availableEvidences, setAvailableEvidences] = useState<EvidenceItem[]>([])

  interface EvidenceItem {
    id: string
    title: string
    evidence_type: string
    file_hash: string | null
  }

  useEffect(() => { selectedOrgIdRef.current = selectedOrgId }, [selectedOrgId])

  useEffect(() => {
    fetchSelections()
    fetchApproachCodes()
  }, [selectedOrgId])

  const fetchSelections = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get("/turbeviis/")
      setSelections(response.data || [])
    } catch (err: any) {
      console.error("Failed to fetch turbeviis selections:", err)
      setError(err.response?.data?.detail || "Failed to load protection modes")
    } finally {
      setLoading(false)
    }
  }

  const fetchApproachCodes = async () => {
    try {
      const response = await apiClient.get("/turbeviis/approaches/list")
      setApproachCodes(response.data)
    } catch (err) {
      console.error("Failed to fetch approach codes:", err)
    }
  }

  const handleSelectApproach = async (approachCode: string) => {
    try {
      const response = await apiClient.post("/turbeviis/", {
        security_approach: approachCode,
      })
      setSelections([response.data, ...selections])
    } catch (err: any) {
      console.error("Failed to create selection:", err)
      alert(err.response?.data?.detail || "Failed to select approach")
    }
  }

  const handleLinkEvidence = async (selectionId: string, evidenceId: string) => {
    try {
      const response = await apiClient.post(`/turbeviis/${selectionId}/link-evidence`, {
        evidence_id: evidenceId,
      })
      setSelections(selections.map(s => s.id === selectionId ? response.data : s))
      setShowEvidenceDialog(false)
      setSelectedSelection(null)
    } catch (err: any) {
      console.error("Failed to link evidence:", err)
      alert(err.response?.data?.detail || "Failed to link evidence")
    }
  }

  const handleUnlinkEvidence = async (selectionId: string) => {
    try {
      const response = await apiClient.delete(`/turbeviis/${selectionId}/unlink-evidence`)
      setSelections(selections.map(s => s.id === selectionId ? response.data : s))
    } catch (err: any) {
      console.error("Failed to unlink evidence:", err)
      alert(err.response?.data?.detail || "Failed to unlink evidence")
    }
  }

  const openEvidenceDialog = async (selection: TurbeviisSelection) => {
    setSelectedSelection(selection)
    try {
      const response = await apiClient.get("/evidences")
      setAvailableEvidences(response.data || [])
      setShowEvidenceDialog(true)
    } catch (err) {
      console.error("Failed to fetch evidences:", err)
    }
  }

  const approachCodeToKey = (code: string): string => {
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
            <h1 className="text-3xl font-bold">{t("turbeviis.title")}</h1>
            <p className="text-muted-foreground mt-1">{t("turbeviis.description")}</p>
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

      {approachCodes && (
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
                        {t(`turbeviis.approaches.${approachKey}.name`)}
                      </Badge>
                      <CardTitle className="mt-2 text-xl">
                        {t(`turbeviis.approaches.${approachKey}.subtitle`)}
                      </CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm">{t(`turbeviis.approaches.${approachKey}.description`)}</p>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">{t("turbeviis.whenToUse")}</h4>
                    <p className="text-xs text-muted-foreground bg-muted p-2 rounded">
                      {t(`turbeviis.approaches.${approachKey}.when`)}
                    </p>
                  </div>

                  {selection ? (
                    <div className="space-y-3 pt-2 border-t">
                      <div className="flex items-center gap-2">
                        {isActive && (
                          <Badge variant="default" className="bg-green-600">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            {t("turbeviis.isActive")}
                          </Badge>
                        )}
                      </div>

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
                          {t("turbeviis.linkEvidence")}
                        </Button>
                      )}
                    </div>
                  ) : (
                    <Button
                      variant="default"
                      className="w-full"
                      onClick={() => handleSelectApproach(approach.code)}
                    >
                      {t("turbeviis.selectApproach")}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {selections.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">{t("turbeviis.activeMode")}</h3>
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
                            {t(`turbeviis.approaches.${approachKey}.name`)}
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
                            {t("turbeviis.approvedBy")}: {selection.approved_by_name}
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
            <DialogTitle>{t("turbeviis.selectEvidence")}</DialogTitle>
            <DialogDescription>
              {t("turbeviis.description")}
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
    </div>
  )
}