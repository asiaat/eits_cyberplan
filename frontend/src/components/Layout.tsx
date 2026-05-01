import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/hooks/use-auth"
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

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/processes", label: "Business Processes", icon: FolderKanban },
  { path: "/assets", label: "Assets", icon: Boxes },
  { path: "/catalog", label: "E-ITS Catalog", icon: BookMarked },
  { path: "/mappings", label: "Mappings", icon: Link2 },
  { path: "/implementation-plan", label: "Implementation Plan", icon: ListTodo },
  { path: "/risks", label: "Risks", icon: AlertTriangle },
  { path: "/evidences", label: "Evidence", icon: FileText },
  { path: "/audit", label: "Audit View", icon: Shield },
  { path: "/admin", label: "Admin", icon: Settings },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

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
        <div className="absolute bottom-0 w-64 p-2 border-t">
          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  )
}