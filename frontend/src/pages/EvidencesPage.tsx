import { useState, useEffect, useRef } from "react"
import { useTranslation } from "@/lib/i18n"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api-client"
import { useAuth } from "@/hooks/use-auth"
import { Upload, Trash2, FileIcon, AlertTriangle, CheckCircle, X } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

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
  created_at: string
  download_url: string | null
}

interface UploadResult {
  id: string
  title: string
  is_new: boolean
  message: string
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
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteId(evidence.id)}
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
                {evidence.file_hash && (
                  <div className="mt-2">
                    <code className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                      SHA256: {evidence.file_hash.substring(0, 16)}...
                    </code>
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

      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
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
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
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