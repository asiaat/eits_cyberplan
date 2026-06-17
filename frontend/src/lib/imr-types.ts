export type PearoStatus = "U" | "P" | "E" | "A" | "R" | "O"

export type ImrPriority = "P1" | "P2" | "P3"

export interface ImrItem {
  id: string
  tenant_id: string
  asset_module_mapping_id?: string
  bp_module_mapping_id?: string
  measure_id: string
  is_process_module_measure: boolean
  pearo_status: PearoStatus
  implementation_description?: string
  non_implementation_justification?: string
  partial_scope_description?: string
  responsible_user_id?: string
  due_date?: string
  next_review_date?: string
  priority: ImrPriority
  risk_acceptance_approved_by?: string
  risk_acceptance_date?: string
  verification_method?: string
  last_verified_at?: string
  created_at: string
  updated_at: string
  measure?: MeasureInfo
  mapped_module_id?: string
  created_by?: string
  updated_by?: string
  status_changed_at?: string
  requirement_profile?: string
  todo_description?: string
  cost_eur?: number
  linked_asset_count?: number
  bp_names: string[]
  asset_names?: string[]
}

export interface MeasureInfo {
  id: string
  code: string
  name: string
  measure_level: string
  module_group?: string
}

export interface ImrItemUpdate {
  pearo_status?: PearoStatus
  implementation_description?: string
  non_implementation_justification?: string
  partial_scope_description?: string
  responsible_user_id?: string
  due_date?: string
  next_review_date?: string
  priority?: ImrPriority
  risk_acceptance_approved_by?: string
  risk_acceptance_date?: string
  verification_method?: string
  last_verified_at?: string
  requirement_profile?: string
  todo_description?: string
  cost_eur?: number
}

export interface ImrValidationStatus {
  can_transition_to_implemented: boolean
  validation_errors: string[]
  linked_evidence_count: number
  has_sufficient_implementation_details: boolean
  imr_item_id: string
  current_status: PearoStatus | null
}

export interface ImrSummaryStatistics {
  pearo_status_counts: Record<PearoStatus, number>
  priority_counts: Record<ImrPriority, number>
  overdue_count: number
  ready_for_completion_count: number
  total_items: number
}

export interface ImrStatusOption {
  value: PearoStatus
  labelKey: string
  color: string
}

export const IMR_STATUS_OPTIONS: ImrStatusOption[] = [
  { value: "U", labelKey: "implementationPlan.status.U", color: "gray" },
  { value: "P", labelKey: "implementationPlan.status.P", color: "slate" },
  { value: "E", labelKey: "implementationPlan.status.E", color: "amber" },
  { value: "A", labelKey: "implementationPlan.status.A", color: "orange" },
  { value: "R", labelKey: "implementationPlan.status.R", color: "emerald" },
  { value: "O", labelKey: "implementationPlan.status.O", color: "blue" },
]

export const IMR_PRIORITY_OPTIONS: { value: ImrPriority; labelKey: string; color: string }[] = [
  { value: "P1", labelKey: "implementationPlan.priority.P1", color: "red" },
  { value: "P2", labelKey: "implementationPlan.priority.P2", color: "orange" },
  { value: "P3", labelKey: "implementationPlan.priority.P3", color: "blue" },
]