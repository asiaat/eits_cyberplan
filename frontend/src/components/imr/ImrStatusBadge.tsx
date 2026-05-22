import { useTranslation } from "@/lib/i18n"
import { PearoStatus } from "@/lib/imr-types"

interface ImrStatusBadgeProps {
  status: PearoStatus | string
  size?: "sm" | "md" | "lg"
}

export function ImrStatusBadge({ status, size = "md" }: ImrStatusBadgeProps) {
  const { t } = useTranslation()
  
  const config = {
    U: { bg: "bg-gray-100", text: "text-gray-700" },
    P: { bg: "bg-slate-100", text: "text-slate-700" },
    E: { bg: "bg-amber-100", text: "text-amber-700" },
    A: { bg: "bg-orange-100", text: "text-orange-700" },
    R: { bg: "bg-emerald-100", text: "text-emerald-700" },
    O: { bg: "bg-blue-100", text: "text-blue-700" },
  }
  
  const style = config[status as keyof typeof config] || { bg: "bg-gray-100", text: "text-gray-700" }
  const label = t(`implementationPlan.status.${status}` as any) || status
  
  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-xs",
    md: "px-2 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  }

  return (
    <span className={`inline-flex items-center rounded-full font-bold ${style.bg} ${style.text} ${sizeClasses[size]}`}>
      {status}
    </span>
  )
}

export function ImrPriorityBadge({ priority }: { priority: string }) {
  const { t } = useTranslation()
  
  const config: Record<string, { bg: string; text: string }> = {
    P1: { bg: "bg-red-100", text: "text-red-700" },
    P2: { bg: "bg-orange-100", text: "text-orange-700" },
    P3: { bg: "bg-blue-100", text: "text-blue-700" },
  }
  
  const style = config[priority] || { bg: "bg-gray-100", text: "text-gray-700" }

  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}>
      {priority} - {t(`implementationPlan.priority.${priority}` as any) || priority}
    </span>
  )
}

export function ImrValidationIndicator({ 
  canTransition, 
  hasEvidence, 
  hasSufficientDetails 
}: { 
  canTransition: boolean
  hasEvidence: boolean
  hasSufficientDetails: boolean
}) {
  const { t } = useTranslation()
  
  if (canTransition) {
    return (
      <span className="inline-flex items-center text-emerald-600" title={t("implementationPlan.validation.canMarkImplemented")}>
        ✓
      </span>
    )
  }

  const issues: string[] = []
  if (!hasSufficientDetails) issues.push(t("implementationPlan.validation.missingDescription"))
  if (!hasEvidence) issues.push(t("implementationPlan.validation.missingEvidence"))

  return (
    <span className="inline-flex items-center text-amber-600" title={issues.join(", ")}>
      ⚠
    </span>
  )
}