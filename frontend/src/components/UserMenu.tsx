import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { useTranslation } from "@/lib/i18n"
import { Settings, LogOut, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

export default function UserMenu() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  const userName = user?.name || "User"
  const userEmail = user?.email || ""
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-ring"
        )}
      >
        <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center">
          <span className="text-xs font-medium text-primary-foreground">
            {initials}
          </span>
        </div>
        <ChevronDown className="h-4 w-4 text-muted-foreground" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-56 rounded-md border bg-popover p-1 shadow-md z-50">
            <div className="px-3 py-2 border-b">
              <p className="font-medium text-sm">{userName}</p>
              <p className="text-xs text-muted-foreground">{userEmail}</p>
            </div>
            <div className="py-1">
              <Link
                to="/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-accent cursor-pointer"
              >
                <Settings className="h-4 w-4" />
                {t("settings.title")}
              </Link>
            </div>
            <div className="border-t py-1">
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-md hover:bg-accent cursor-pointer text-red-500"
              >
                <LogOut className="h-4 w-4" />
                {t("nav.logout")}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}