import { useState, useEffect } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
import { useTranslation } from "@/lib/i18n"
import LanguageSelector from "@/lib/i18n/LanguageSelector"
import ThemeToggle from "@/components/ThemeToggle"
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
  BookOpen,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"

const SIDEBAR_STORAGE_KEY = "eits-sidebar-collapsed"

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
    { path: "/terminology", label: t("nav.terminology"), icon: BookOpen },
    { path: "/admin", label: t("nav.admin"), icon: Settings },
  ]
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const navItems = getNavItems(t)

  const [collapsed, setCollapsed] = useState(() => {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY)
    return stored === "true"
  })

  useEffect(() => {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed))
  }, [collapsed])

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <div className="min-h-screen flex">
      <aside
        className={cn(
          "border-r bg-card flex flex-col transition-all duration-500",
          collapsed ? "w-16" : "w-64"
        )}
      >
        <div className={cn(
          "p-4 border-b flex items-center justify-between",
          collapsed ? "justify-center" : ""
        )}>
          {collapsed ? (
            <h1 className="text-xl font-cyber font-bold text-primary cyber-glow-subtle">
              CP
            </h1>
          ) : (
            <h1 className="text-2xl font-cyber font-bold text-primary cyber-glow-subtle tracking-wider">
              CYBER<span className="text-primary">PLAN</span>
            </h1>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={cn(
              "p-1 rounded-md hover:bg-accent transition-colors",
              collapsed ? "absolute left-12" : ""
            )}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <ChevronLeft className="h-5 w-5" />
            )}
          </button>
        </div>
        <nav className={cn("p-2 flex-1", collapsed ? "px-1" : "")}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-accent transition-all duration-500",
                location.pathname === item.path && "bg-accent",
                collapsed ? "justify-center" : ""
              )}
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          ))}
        </nav>
        <div className={cn(
          "p-2 border-t flex flex-col gap-2",
          collapsed ? "items-center" : ""
        )}>
          {collapsed ? (
            <div className="flex flex-col gap-2">
              <ThemeToggle />
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <LanguageSelector />
              <ThemeToggle />
            </div>
          )}
          <Button
            variant="ghost"
            className={cn(
              "w-full justify-start hover:bg-accent transition-all duration-500",
              collapsed ? "px-2 justify-center" : ""
            )}
            onClick={handleLogout}
            title={collapsed ? t("nav.logout") : undefined}
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && <span className="ml-2">{t("nav.logout")}</span>}
          </Button>
        </div>
      </aside>
      <main className={cn(
        "flex-1 p-8 transition-all duration-500",
        collapsed ? "ml-16" : "ml-64"
      )}>
        {children}
      </main>
    </div>
  )
}