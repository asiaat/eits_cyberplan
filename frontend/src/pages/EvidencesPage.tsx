import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Upload, Trash2, FileIcon, AlertTriangle, CheckCircle, X, Download, ExternalLink } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface LinkedBP {
  process_id: string
  process_name: string
  link_id: string
}

interface LinkedImrItem {
  imr_item_id: string
  measure_code: string
  measure_name: string
  link_id: string
}

interface EvidenceItem {
  id: string
  title: string
  evidence_type: string
  storage_uri: string | null
  external_url: string | null
  file_hash: string | null
  version: string | null
  owner_name: string | null
  valid_from: string | null
  valid_until: string | null
  review_due_date: string | null
  file_size: number | null
  mime_type: string | null
  download_count: number
  created_at: string
  download_url: string | null
  linked_business_processes: LinkedBP[]
  linked_imr_items: LinkedImrItem[]
}

interface UploadResult {
  id: string
  title: string
  is_new: boolean
  message: string
}

const formatFileSize = (bytes: number | null): string => {
  if (bytes === null || bytes === undefined) return ""
  const units = ["B", "KB", "MB", "GB"]
  let value = bytes
  let unitIdx = 0
  while (value >= 1024 && unitIdx < units.length - 1) {
    value /= 1024
    unitIdx++
  }
  return `${value.toFixed(value >= 100 ? 0 : value >= 10 ? 1 : 2)} ${units[unitIdx]}`
}

const getFileExtension = (mimeType: string | null): string => {
  if (!mimeType) return ""
  const map: Record<string, string> = {
    "application/pdf": "PDF",
    "application/msword": "DOC",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/vnd.ms-excel": "XLS",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
    "image/jpeg": "JPG",
    "image/png": "PNG",
    "text/plain": "TXT",
  }
  return map[mimeType] || mimeType.split("/").pop()?.toUpperCase() || ""
}

const evidenceTypeColors: Record<string, string> = {
  document: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200",
  url: "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900 dark:text-purple-200",
  note: "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-200",
}

export default function EvidencesPage() {
  const { t } = useTranslation()
  const { selectedOrgId } = useAuth()
  const selectedOrgIdRef = useRef(selectedOrgId)
  const [evidences, setEvidences] = useState<EvidenceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [showUpload, setShowUpload] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deletingEvidence, setDeletingEvidence] = useState<EvidenceItem | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [title, setTitle] = useState("")
  const [evidenceType, setEvidenceType] = useState("document")

  useEffect(() => { selectedOrgIdRef.current = selectedOrgId }, [selectedOrgId])

  useEffect(() => {
    fetchEvidences()
  }, [selectedOrgId])

  const fetchEvidences = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get("/evidences")
      setEvidences(response.data || [])
    } catch (err: any) {
      console.error("Failed to fetch evidences:", err)
      setError(err.response?.data?.detail || "Failed to load evidences")
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, ""))
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !title) return

    try {
      setUploading(true)
      setUploadResult(null)

      const formData = new FormData()
      formData.append("file", selectedFile)
      formData.append("title", title)
      formData.append("evidence_type", evidenceType)

      const response = await apiClient.post("/evidences/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })

      const result = response.data

      if (result.is_new) {
        setUploadResult({
          id: result.id,
          title: result.title,
          is_new: true,
          message: t("evidences.uploadSuccess"),
        })
      } else {
        setUploadResult({
          id: result.id,
          title: result.title,
          is_new: false,
          message: t("evidences.fileExists"),
        })
      }

      setSelectedFile(null)
      setTitle("")
      fetchEvidences()
    } catch (err: any) {
      console.error("Upload failed:", err)
      setError(err.response?.data?.detail || "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await apiClient.delete(`/evidences/${id}`)
      setDeleteId(null)
      fetchEvidences()
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete")
    }
  }

  const handleDownload = async (id: string, title: string) => {
    try {
      const response = await apiClient.get(`/evidences/${id}/download`, {
        responseType: "blob",
      })
      const disposition = response.headers["content-disposition"]
      const match = disposition?.match(/filename="(.+)"/)
      const filename = match ? match[1] : `${title}.pdf`
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error("Download failed:", err)
    }
  }

  const filteredEvidences = evidences.filter((e) =>
    e.title.toLowerCase().includes(search.toLowerCase())
  )

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    return new Date(dateStr).toLocaleDateString()
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
          <h1 className="text-3xl font-bold">{t("evidences.title")}</h1>
          <Badge variant="outline" className="bg-primary/10 text-primary">
            {evidences.length} {t("evidences.items")}
          </Badge>
        </div>
        <Button onClick={() => setShowUpload(true)}>
          <Upload className="h-4 w-4 mr-2" />
          {t("evidences.uploadNew")}
        </Button>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-4">
        <Input
          placeholder={t("evidences.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {filteredEvidences.length === 0 && !error ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <FileIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">{t("evidences.noData")}</p>
              <Button onClick={() => setShowUpload(true)} variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                {t("evidences.uploadFirst")}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredEvidences.map((evidence) => (
            <Card key={evidence.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <FileIcon className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <CardTitle className="text-xl">{evidence.title}</CardTitle>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className={evidenceTypeColors[evidence.evidence_type] || "bg-gray-100"}>
                          {evidence.evidence_type}
                        </Badge>
                        {evidence.version && (
                          <span className="text-sm text-muted-foreground">v{evidence.version}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {evidence.evidence_type === "document" && (
                      <button
                        onClick={() => handleDownload(evidence.id, evidence.title)}
                        className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    )}
                    {evidence.evidence_type === "url" && evidence.external_url && (
                      <a
                        href={evidence.external_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                        title="Open URL"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setDeleteId(evidence.id)
                        setDeletingEvidence(evidence)
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  {evidence.owner_name && (
                    <span>{t("evidences.owner")}: {evidence.owner_name}</span>
                  )}
                  {evidence.created_at && (
                    <span>{t("evidences.uploaded")}: {formatDate(evidence.created_at)}</span>
                  )}
                  {evidence.valid_until && (
                    <span>{t("evidences.validUntil")}: {formatDate(evidence.valid_until)}</span>
                  )}
                  {evidence.review_due_date && (
                    <span>{t("evidences.reviewDue")}: {formatDate(evidence.review_due_date)}</span>
                  )}
                </div>
                {(evidence.file_size || evidence.mime_type || evidence.download_count > 0) && (
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                    {evidence.mime_type && (
                      <Badge variant="secondary" className="text-xs font-mono">
                        {getFileExtension(evidence.mime_type)}
                      </Badge>
                    )}
                    {evidence.file_size != null && (
                      <span>{formatFileSize(evidence.file_size)}</span>
                    )}
                    {evidence.download_count > 0 && (
                      <span>{evidence.download_count} download{evidence.download_count !== 1 ? "s" : ""}</span>
                    )}
                  </div>
                )}
                {evidence.file_hash && (
                  <div className="mt-2">
                    <code className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                      SHA256: {evidence.file_hash.substring(0, 16)}...
                    </code>
                  </div>
                )}
                {evidence.linked_business_processes && evidence.linked_business_processes.length > 0 && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-muted-foreground">{t("evidences.linkedTo") || "Linked to"}:</span>
                    {evidence.linked_business_processes.map((bp) => (
                      <Badge key={bp.link_id} variant="outline" className="text-xs">
                        {bp.process_name}
                      </Badge>
                    ))}
                  </div>
                )}
                {evidence.linked_imr_items && evidence.linked_imr_items.length > 0 && (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-muted-foreground">IMR:</span>
                    {evidence.linked_imr_items.map((item) => (
                      <Badge key={item.link_id} variant="outline" className="text-xs">
                        {item.measure_code}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={showUpload} onOpenChange={(open) => {
        setShowUpload(open)
        if (!open) {
          setSelectedFile(null)
          setTitle("")
          setUploadResult(null)
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("evidences.uploadTitle")}</DialogTitle>
            <DialogDescription>
              {t("evidences.uploadDesc")}
            </DialogDescription>
          </DialogHeader>

          {uploadResult && (
            <div className={`p-4 rounded-lg mb-4 flex items-start gap-3 ${
              uploadResult.is_new 
                ? "bg-green-50 border border-green-200 dark:bg-green-900/20" 
                : "bg-yellow-50 border border-yellow-200 dark:bg-yellow-900/20"
            }`}>
              {uploadResult.is_new ? (
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              )}
              <div>
                <p className="font-medium">{uploadResult.title}</p>
                <p className="text-sm text-muted-foreground">{uploadResult.message}</p>
              </div>
              <button 
                onClick={() => setUploadResult(null)}
                className="ml-auto text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">{t("evidences.file") || "File"} *</label>
              <input
                type="file"
                onChange={handleFileSelect}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt"
              />
              {selectedFile && (
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium">{t("common.name")} *</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={t("evidences.titlePlaceholder")}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">{t("common.type")}</label>
              <select
                value={evidenceType}
                onChange={(e) => setEvidenceType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm mt-1"
              >
                <option value="document">{t("evidences.typeDocument")}</option>
                <option value="url">{t("evidences.typeUrl")}</option>
                <option value="note">{t("evidences.typeNote")}</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUpload(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || !title || uploading}
            >
              {uploading ? t("common.uploading") || "Uploading..." : t("common.upload") || "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!deleteId} onOpenChange={(open) => {
        if (!open) { setDeleteId(null); setDeletingEvidence(null) }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
              {t("evidences.deleteTitle")}
            </DialogTitle>
            <DialogDescription>
              {t("evidences.deleteConfirm")}
            </DialogDescription>
          </DialogHeader>
          {deletingEvidence && (
            <div className="space-y-3 py-2">
              {(deletingEvidence.linked_business_processes.length > 0 || deletingEvidence.linked_imr_items.length > 0) && (
                <p className="text-sm text-amber-600 dark:text-amber-400">
                  {t("evidences.deleteWarning")}
                </p>
              )}
              {deletingEvidence.linked_business_processes.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">{t("evidences.linkedTo") || "Linked to"}:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {deletingEvidence.linked_business_processes.map((bp) => (
                      <Badge key={bp.link_id} variant="outline" className="text-xs">
                        {bp.process_name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {deletingEvidence.linked_imr_items.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">IMR:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {deletingEvidence.linked_imr_items.map((item) => (
                      <Badge key={item.link_id} variant="outline" className="text-xs">
                        {item.measure_code}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => { setDeleteId(null); setDeletingEvidence(null) }}>
              {t("common.cancel")}
            </Button>
            <Button variant="destructive" onClick={() => deleteId && handleDelete(deleteId)}>
              {t("common.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}