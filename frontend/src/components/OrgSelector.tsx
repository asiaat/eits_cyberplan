import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { useTranslation } from "@/lib/i18n"
import { Building2, ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

export default function OrgSelector() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { organizations, selectedOrgId, selectOrg } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  const currentOrg = organizations.find((org) => org.id === selectedOrgId)

  const handleSelectOrg = (orgId: string) => {
    selectOrg(orgId)
    setIsOpen(false)
  }

  const isOnLoginPage = window.location.pathname === "/login"
  const isOnSelectOrgPage = window.location.pathname === "/select-org"

  if (isOnLoginPage || isOnSelectOrgPage) {
    return null
  }

  if (!selectedOrgId) {
    return (
      <button
        onClick={() => navigate("/select-org")}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-yellow-500 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 transition-colors"
      >
        <Building2 className="h-4 w-4" />
        <span className="text-sm font-medium">
          {t("selectOrg.select") || "Select Organization"}
        </span>
        <ChevronDown className="h-3 w-3" />
      </button>
    )
  }

  if (organizations.length === 1) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-primary/10 border border-primary/20 text-primary">
        <Building2 className="h-4 w-4" />
        <span className="text-sm font-medium max-w-[150px] truncate">
          {currentOrg?.name || "Organization"}
        </span>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-md",
          "bg-primary/10 border border-primary/20 hover:bg-primary/20",
          "text-primary transition-colors"
        )}
      >
        <Building2 className="h-4 w-4" />
        <span className="text-sm font-medium max-w-[150px] truncate">
          {currentOrg?.name || "Organization"}
        </span>
        <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-64 rounded-md border bg-popover p-1 shadow-md z-50">
            <div className="px-3 py-2 border-b">
              <p className="text-xs text-muted-foreground font-medium">
                {t("selectOrg.switchOrg") || "Switch Organization"}
              </p>
            </div>
            <div className="py-1 max-h-[300px] overflow-y-auto">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSelectOrg(org.id)}
                  className={cn(
                    "flex items-center justify-between w-full px-3 py-2 text-sm rounded-md",
                    "hover:bg-accent cursor-pointer",
                    org.id === selectedOrgId && "bg-accent"
                  )}
                >
                  <span className="truncate">{org.name}</span>
                  {org.id === selectedOrgId && (
                    <Check className="h-4 w-4 text-primary flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
            {organizations.length > 1 && (
              <div className="border-t py-1">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    navigate("/select-org")
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md hover:bg-accent cursor-pointer text-muted-foreground"
                >
                  {t("selectOrg.viewAll") || "View all organizations"}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}