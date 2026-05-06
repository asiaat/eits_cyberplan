import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { useTranslation } from "@/lib/i18n"
import LanguageSelector from "@/lib/i18n/LanguageSelector"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  FolderKanban,
  Boxes,
  BookMarked,
  Link2,
  ListTodo,
  AlertTriangle,
  FileText,
  Shield,
  Settings,
  LogOut,
} from "lucide-react"
import { cn } from "@/lib/utils"

function getNavItems(t: (key: string) => string) {
  return [
    { path: "/", label: t("nav.dashboard"), icon: LayoutDashboard },
    { path: "/processes", label: t("nav.businessProcesses"), icon: FolderKanban },
    { path: "/assets", label: t("nav.assets"), icon: Boxes },
    { path: "/catalog", label: t("nav.catalog"), icon: BookMarked },
    { path: "/mappings", label: t("nav.mappings"), icon: Link2 },
    { path: "/implementation-plan", label: t("nav.implementationPlan"), icon: ListTodo },
    { path: "/risks", label: t("nav.risks"), icon: AlertTriangle },
    { path: "/evidences", label: t("nav.evidence"), icon: FileText },
    { path: "/audit", label: t("nav.auditView"), icon: Shield },
    { path: "/admin", label: t("nav.admin"), icon: Settings },
  ]
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const navItems = getNavItems(t)

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 border-r bg-card">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold">E-ITS</h1>
        </div>
        <nav className="p-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-accent",
                location.pathname === item.path && "bg-accent"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="absolute bottom-0 w-64 p-2 border-t flex flex-col gap-2">
          <LanguageSelector />
          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            {t("nav.logout")}
          </Button>
        </div>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  )
}