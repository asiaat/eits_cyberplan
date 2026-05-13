import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/use-auth"
import { useTranslation } from "@/lib/i18n"
import { Building2 } from "lucide-react"

export default function SelectOrgPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { organizations, selectOrg, loading } = useAuth()

  const handleSelectOrg = (orgId: string) => {
    selectOrg(orgId)
    navigate("/", { replace: true })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p>{t("common.loading")}</p>
      </div>
    )
  }

  if (!organizations || organizations.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">No organizations found. Please contact your administrator.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 p-3 bg-primary/10 rounded-full w-fit">
            <Building2 className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-cyber font-bold tracking-wider cyber-glow-subtle">
            {t("selectOrg.title") || "Select Organization"}
          </CardTitle>
          <p className="text-muted-foreground mt-2">
            {t("selectOrg.description") || "Please select an organization to continue"}
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {organizations.map((org) => (
              <Button
                key={org.id}
                variant="outline"
                className="h-auto py-6 flex flex-col items-center justify-center gap-2 hover:bg-accent hover:border-primary transition-all"
                onClick={() => handleSelectOrg(org.id)}
              >
                <Building2 className="h-6 w-6" />
                <span className="text-lg font-medium">{org.name}</span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}