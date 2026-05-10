import { useState, useEffect } from "react"
import { Link, useLocation } from "react-router-dom"
import { useTranslation } from "@/lib/i18n"
import LanguageSelector from "@/lib/i18n/LanguageSelector"
import ThemeToggle from "@/components/ThemeToggle"
import UserMenu from "@/components/UserMenu"
import OrgSelector from "@/components/OrgSelector"
import AlertBell from "@/components/AlertBell"
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
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Users,
  UserCog,
} from "lucide-react"
import { cn } from "@/lib/utils"

const SIDEBAR_STORAGE_KEY = "eits-sidebar-collapsed"

interface NavItem {
  path: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

interface NavSection {
  key: string
  items: NavItem[]
}

function getNavSections(t: (key: string) => string): NavSection[] {
  return [
    {
      key: "eits",
      items: [
        { path: "/", label: t("nav.dashboard"), icon: LayoutDashboard },
        { path: "/processes", label: t("nav.businessProcesses"), icon: FolderKanban },
        { path: "/assets", label: t("nav.assets"), icon: Boxes },
        { path: "/catalog", label: t("nav.catalog"), icon: BookMarked },
        { path: "/mappings", label: t("nav.mappings"), icon: Link2 },
        { path: "/implementation-plan", label: t("nav.implementationPlan"), icon: ListTodo },
      ]
    },
    {
      key: "risk",
      items: [
        { path: "/risks", label: t("nav.risks"), icon: AlertTriangle },
        { path: "/evidences", label: t("nav.evidence"), icon: FileText },
      ]
    },
    {
      key: "support",
      items: [
        { path: "/audit", label: t("nav.auditView"), icon: Shield },
        { path: "/terminology", label: t("nav.terminology"), icon: BookOpen },
        { path: "/organization", label: t("nav.organization"), icon: Users },
      ]
    },
  ]
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation()
  const location = useLocation()
  const navSections = getNavSections(t)

  const [collapsed, setCollapsed] = useState(() => {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY)
    return stored === "true"
  })

  useEffect(() => {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed))
  }, [collapsed])

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
        <nav className={cn("p-2 flex-1 overflow-y-auto", collapsed ? "px-1" : "")}>
          {navSections.map((section, sectionIdx) => (
            <div key={section.key} className={cn("mb-4", sectionIdx === 0 && "mt-2")}>
              {!collapsed && (
                <div className="px-3 mb-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {t(`nav.section.${section.key}`)}
                  </span>
                </div>
              )}
              {section.items.map((item) => (
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
              {collapsed && sectionIdx < navSections.length - 1 && (
                <div className="border-b my-2 mx-2" />
              )}
            </div>
          ))}
        </nav>
        <div className={cn(
          "p-2 border-t",
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
        </div>
      </aside>
      <div className="flex-1 flex flex-col">
        <header className="border-b p-4 flex items-center justify-between gap-4">
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <AlertBell />
            <OrgSelector />
            <UserMenu />
          </div>
        </header>
        <main className={cn(
          "p-8 transition-all duration-500",
          collapsed ? "ml-16" : "ml-64"
        )}>
          {children}
        </main>
      </div>
    </div>
  )
}