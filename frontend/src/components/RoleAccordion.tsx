import { useState, useEffect } from "react"
import { useTranslation } from "@/lib/i18n"
import { ChevronDown, ChevronRight, Edit2, Trash2, Save, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Permission {
  id: string
  code: string
  name: string
  category: string | null
}

interface RoleAccordionProps {
  role: {
    id: string
    role_name: string
    description: string | null
  }
  allPermissions: Permission[]
  assignedPermissions: string[]
  canEdit: boolean
  isExpanded: boolean
  onToggleExpand: () => void
  isEditing: boolean
  onStartEdit: () => void
  onCancelEdit: () => void
  onSave: (name: string, desc: string) => void
  onTogglePermission: (permId: string, added: boolean) => void
  onDelete: () => void
  hasPermissionChanges: boolean
}

export default function RoleAccordion({
  role,
  allPermissions,
  assignedPermissions,
  canEdit,
  isExpanded,
  onToggleExpand,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onSave,
  onTogglePermission,
  onDelete,
  hasPermissionChanges,
}: RoleAccordionProps) {
  const { t } = useTranslation()
  const [editName, setEditName] = useState(role.role_name)
  const [editDesc, setEditDesc] = useState(role.description || "")
  const [localAssigned, setLocalAssigned] = useState<string[]>(assignedPermissions)
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set())

  useEffect(() => {
    setEditName(role.role_name)
    setEditDesc(role.description || "")
  }, [role.role_name, role.description])

  useEffect(() => {
    setLocalAssigned(assignedPermissions)
  }, [assignedPermissions])

  const allCategories = [...new Set(allPermissions.map(p => p.category || "other"))].sort()

  const getPermissionsForCategory = (cat: string) => {
    return allPermissions.filter(p => (p.category || "other") === cat)
  }

  const getCategoryCount = (cat: string) => {
    return localAssigned.filter(id => 
      getPermissionsForCategory(cat).some(p => p.id === id)
    ).length
  }

  const toggleCategory = (cat: string) => {
    const newSet = new Set(collapsedCategories)
    if (newSet.has(cat)) {
      newSet.delete(cat)
    } else {
      newSet.add(cat)
    }
    setCollapsedCategories(newSet)
  }

  const handleTogglePermission = (permId: string) => {
    const isAssigned = localAssigned.includes(permId)
    setLocalAssigned(prev => 
      isAssigned ? prev.filter(id => id !== permId) : [...prev, permId]
    )
    onTogglePermission(permId, isAssigned)
  }

  const handleSave = () => {
    onSave(editName, editDesc)
  }

  const handleCancel = () => {
    setEditName(role.role_name)
    setEditDesc(role.description || "")
    setLocalAssigned(assignedPermissions)
    onCancelEdit()
  }

  const handleDelete = () => {
    if (confirm(t("admin.deleteConfirm"))) {
      onDelete()
    }
  }

  return (
    <div className={`border rounded-lg overflow-hidden transition-colors ${isExpanded ? 'bg-card' : ''}`}>
      {/* Header - Clickable to expand/collapse */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-3 flex-1">
          {/* Expand/Collapse Icon */}
          <span className="text-muted-foreground">
            {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </span>
          
          {/* Role Info */}
          <div className="flex-1">
            {isEditing ? (
              <div className="space-y-1" onClick={e => e.stopPropagation()}>
                <input
                  type="text"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  className="w-full font-semibold text-lg border rounded px-2 py-1"
                  placeholder={t("admin.roleName")}
                />
                <textarea
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                  className="w-full text-sm border rounded px-2 py-1"
                  rows={2}
                  placeholder={t("admin.description")}
                />
              </div>
            ) : (
              <>
                <h3 className="font-semibold text-lg">{role.role_name}</h3>
                {role.description && (
                  <p className="text-sm text-muted-foreground">{role.description}</p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
          {/* Permission count badge */}
          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
            {localAssigned.length} permissions
          </span>

          {/* Edit/Delete buttons (only when expanded and can edit) */}
          {isExpanded && canEdit && !isEditing && (
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" onClick={onStartEdit}>
                <Edit2 className="h-4 w-4 mr-1" />
                {t("admin.edit")}
              </Button>
              <Button variant="ghost" size="sm" onClick={handleDelete} className="text-destructive hover:text-destructive">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Save/Cancel buttons (when editing) */}
          {isEditing && (
            <div className="flex gap-1">
              <Button variant="default" size="sm" onClick={handleSave}>
                <Save className="h-4 w-4 mr-1" />
                {t("admin.save")}
              </Button>
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <X className="h-4 w-4 mr-1" />
                {t("admin.cancel")}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t bg-background">
          <div className="pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-sm text-muted-foreground uppercase">{t("admin.permissions")}</h4>
              {hasPermissionChanges && !isEditing && (
                <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                  {t("admin.unsavedChanges")}
                </span>
              )}
            </div>

            <div className="space-y-2">
              {allCategories.map(cat => {
                const catPerms = getPermissionsForCategory(cat)
                const assignedCount = getCategoryCount(cat)
                const isCollapsed = collapsedCategories.has(cat)

                return (
                  <div key={cat} className="border rounded">
                    {/* Category Header */}
                    <button
                      onClick={() => toggleCategory(cat)}
                      className="flex items-center w-full p-2 text-sm font-medium hover:bg-muted/50 transition-colors"
                    >
                      {isCollapsed ? (
                        <ChevronRight className="h-4 w-4 mr-2 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 mr-2 text-muted-foreground" />
                      )}
                      <span className="capitalize">{cat}</span>
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                        assignedCount > 0 
                          ? 'bg-primary/10 text-primary' 
                          : 'bg-muted text-muted-foreground'
                      }`}>
                        {assignedCount}
                      </span>
                    </button>

                    {/* Category Permissions */}
                    {!isCollapsed && (
                      <div className="px-4 pb-2 flex flex-wrap gap-2">
                        {catPerms.map(perm => {
                          const isAssigned = localAssigned.includes(perm.id)
                          return (
                            <label
                              key={perm.id}
                              className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded cursor-pointer transition-colors ${
                                isAssigned 
                                  ? 'bg-primary text-primary-foreground' 
                                  : 'bg-secondary hover:bg-secondary/80'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isAssigned}
                                onChange={() => handleTogglePermission(perm.id)}
                                className="sr-only"
                              />
                              <span className={!isAssigned ? 'opacity-60' : ''}>{perm.name}</span>
                            </label>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}