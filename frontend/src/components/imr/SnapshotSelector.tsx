import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api-client"
import { useTranslation } from "@/lib/i18n"
import { History, Eye } from "lucide-react"

interface Snapshot {
  id: string
  label: string
  description: string | null
  item_count: number
  created_at: string
  created_by_name: string | null
  pm_approach: string | null
  is_current: boolean
}

interface SnapshotSelectorProps {
  selectedSnapshotId: string | null
  onSelectSnapshot: (snapshotId: string | null) => void
}

export function SnapshotSelector({ selectedSnapshotId, onSelectSnapshot }: SnapshotSelectorProps) {
  const { t } = useTranslation()
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadSnapshots()
  }, [])

  const loadSnapshots = async () => {
    setLoading(true)
    try {
      const res = await apiClient.get("/imr-snapshots/")
      setSnapshots(res.data.snapshots || [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const selectedSnapshot = snapshots.find((s) => s.id === selectedSnapshotId)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
          selectedSnapshotId
            ? "bg-amber-50 dark:bg-amber-950 border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200"
            : "bg-card border-border text-muted-foreground hover:text-foreground"
        }`}
        title={selectedSnapshotId ? "Viewing historical snapshot" : "Current working version"}
      >
        <History className="w-4 h-4" />
        <span>
          {selectedSnapshotId
            ? selectedSnapshot?.label || "Snapshot"
            : t("implementationPlan.currentVersion") || "Current"}
        </span>
        {selectedSnapshotId && (
          <span className="text-xs opacity-70">({selectedSnapshot?.item_count ?? "?"})</span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 w-80 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
            <div className="p-2 border-b border-border bg-muted/50">
              <button
                onClick={() => {
                  onSelectSnapshot(null)
                  setIsOpen(false)
                }}
                className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 transition-colors ${
                  !selectedSnapshotId ? "bg-primary/10 text-primary" : "hover:bg-muted"
                }`}
              >
                <Eye className="w-4 h-4" />
                <span className="font-medium">{t("implementationPlan.currentVersion") || "Current Working Version"}</span>
              </button>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {snapshots.length === 0 && !loading && (
                <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                  No snapshots yet. Snapshots are created automatically when protection mode changes.
                </div>
              )}
              {loading && (
                <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                  Loading...
                </div>
              )}
              {snapshots.map((snap) => (
                <button
                  key={snap.id}
                  onClick={() => {
                    onSelectSnapshot(snap.id)
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2.5 border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors ${
                    selectedSnapshotId === snap.id ? "bg-amber-50 dark:bg-amber-950" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{snap.label}</span>
                    <span className="text-xs text-muted-foreground">{snap.item_count} items</span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    {snap.pm_approach && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                        {snap.pm_approach}
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {new Date(snap.created_at).toLocaleDateString()}
                    </span>
                    {snap.created_by_name && (
                      <span className="text-xs text-muted-foreground">by {snap.created_by_name}</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
