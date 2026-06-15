import { useTranslation } from "@/lib/i18n"
import { ImrDashboardStats } from "@/components/imr/ImrDashboardStats"
import BusinessProcessStats from "@/components/dashboard/BusinessProcessStats"
import AssetStats from "@/components/dashboard/AssetStats"
import ScopeStats from "@/components/dashboard/ScopeStats"

export default function DashboardPage() {
  const { t } = useTranslation()

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">{t("dashboard.title")}</h1>

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          {t("dashboard.section.scopeModelling")}
        </h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 items-stretch">
          <BusinessProcessStats />
          <AssetStats />
          <ScopeStats />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          {t("dashboard.section.imr")}
        </h2>
        <ImrDashboardStats />
      </section>
    </div>
  )
}
