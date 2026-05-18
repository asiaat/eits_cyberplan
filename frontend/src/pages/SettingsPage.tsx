import { useTranslation } from "@/lib/i18n"
import { useTheme } from "@/lib/use-theme"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useState, useEffect } from "react"
import { Settings, Palette, Globe, Layout, User, Shield } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"

const SIDEBAR_STORAGE_KEY = "eits-sidebar-collapsed"

export default function SettingsPage() {
  const { t } = useTranslation()
  const { theme, setTheme } = useTheme()
  const { user } = useAuth()
  
  const [language, setLanguage] = useState<string>("en")
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false)

  useEffect(() => {
    const storedLang = localStorage.getItem("eits-language")
    if (storedLang === "en" || storedLang === "ee") {
      setLanguage(storedLang)
    }
    
    const storedSidebar = localStorage.getItem(SIDEBAR_STORAGE_KEY)
    setSidebarCollapsed(storedSidebar === "true")
  }, [])

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang)
    localStorage.setItem("eits-language", lang)
    window.location.reload()
  }

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme as "light" | "dark" | "system")
  }

  const handleSidebarChange = (checked: boolean) => {
    setSidebarCollapsed(checked)
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(checked))
  }

  const userRoles = JSON.parse(localStorage.getItem("user_roles") || "[]")

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* User Info Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            {t("settings.userInfo") || "User Information"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between">
            <span className="text-muted-foreground">{t("common.email") || "Email"}:</span>
            <span className="font-medium">{user?.email || localStorage.getItem("user_email")}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">{t("common.name") || "Name"}:</span>
            <span className="font-medium">{user?.name || localStorage.getItem("user_full_name")}</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{t("settings.roles") || "Roles"}:</span>
            <div className="flex flex-wrap gap-1">
              {userRoles && userRoles.length > 0 ? (
                userRoles.map((role: any, index: number) => (
                  <span key={index} className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                    {t(`settings.roleNames.${role.role_name}`) || role.role_name}
                  </span>
                ))
              ) : (
                <span className="text-xs text-muted-foreground">{t("settings.noRoles") || "No roles assigned"}</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Settings className="h-8 w-8" />
        <h1 className="text-3xl font-bold">{t("settings.title")}</h1>
      </div>

      {/* Appearance Section */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Palette className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{t("settings.appearance")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="theme-select">{t("settings.theme")}</Label>
            <Select value={theme} onValueChange={handleThemeChange}>
              <SelectTrigger id="theme-select" className="w-full">
                <SelectValue placeholder={t("settings.theme")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">{t("settings.themeLight")}</SelectItem>
                <SelectItem value="dark">{t("settings.themeDark")}</SelectItem>
                <SelectItem value="system">{t("settings.themeSystem")}</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              {theme === "light" && t("settings.themeLightDesc")}
              {theme === "dark" && t("settings.themeDarkDesc")}
              {theme === "system" && t("settings.themeSystemDesc")}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Language Section */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Globe className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{t("settings.language")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="language-select">{t("settings.defaultLanguage")}</Label>
            <Select value={language} onValueChange={handleLanguageChange}>
              <SelectTrigger id="language-select" className="w-full">
                <SelectValue placeholder={t("settings.defaultLanguage")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">{t("settings.english")}</SelectItem>
                <SelectItem value="ee">{t("settings.estonian")}</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              {t("settings.languageDesc")}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Display Section */}
      <Card>
        <CardHeader className="flex flex-row items-center gap-2">
          <Layout className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{t("settings.display")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="sidebar-toggle">{t("settings.sidebarCollapsed")}</Label>
              <p className="text-sm text-muted-foreground">
                {t("settings.sidebarCollapsedDesc")}
              </p>
            </div>
            <Switch
              id="sidebar-toggle"
              checked={sidebarCollapsed}
              onCheckedChange={handleSidebarChange}
            />
          </div>
        </CardContent>
      </Card>

      {/* About Section */}
      <Card>
        <CardHeader>
          <CardTitle>{t("settings.about")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("settings.version")}</span>
            <span>1.0.0</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("settings.system")}</span>
            <span>E-ITS Management System</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}