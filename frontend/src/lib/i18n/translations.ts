export const translations = {
  en: {
    common: {
      loading: "Loading...",
      noData: "No data yet.",
      save: "Save",
      cancel: "Cancel",
      delete: "Delete",
      edit: "Edit",
      add: "Add",
      search: "Search",
      actions: "Actions",
    },
    nav: {
      dashboard: "Dashboard",
      businessProcesses: "Business Processes",
      assets: "Assets",
      catalog: "E-ITS Catalog",
      mappings: "Mappings",
      implementationPlan: "Implementation Plan",
      risks: "Risks",
      evidence: "Evidence",
      auditView: "Audit View",
      admin: "Admin",
      logout: "Logout",
    },
    login: {
      title: "E-ITS Management System",
      email: "Email",
      password: "Password",
      signIn: "Sign In",
      signingIn: "Signing in...",
      invalidCredentials: "Invalid email or password",
    },
    dashboard: {
      title: "Dashboard",
      totalMeasures: "Total Measures",
      implemented: "Implemented",
      inProgress: "In Progress",
      notStarted: "Not Started",
      overdueTasks: "Overdue Tasks",
      highRisks: "High Risks",
      noOverdueTasks: "No overdue tasks",
      noHighRisks: "No high risks",
    },
    businessProcesses: {
      title: "Business Processes",
      noData: "No business processes yet.",
    },
    assets: {
      title: "Assets",
      noData: "No assets yet.",
    },
    catalog: {
      title: "E-ITS Catalog",
      noData: "No catalog items yet.",
    },
    mappings: {
      title: "Mappings",
      noData: "No mappings yet.",
    },
    implementationPlan: {
      title: "Implementation Plan",
      noData: "No implementation items yet.",
    },
    risks: {
      title: "Risk Register",
      noData: "No risks registered yet.",
    },
    evidences: {
      title: "Evidence",
      noData: "No evidence uploaded yet.",
    },
    auditView: {
      title: "Audit View",
      noData: "No data for audit view.",
    },
    admin: {
      title: "Admin",
      noData: "Admin panel placeholder.",
    },
  },
  ee: {
    common: {
      loading: "Laadimine...",
      noData: "Andmeid veel ei ole.",
      save: "Salvesta",
      cancel: "Tühista",
      delete: "Kustuta",
      edit: "Muuda",
      add: "Lisa",
      search: "Otsi",
      actions: "Tegevused",
    },
    nav: {
      dashboard: "Töölaud",
      businessProcesses: "Äriprotsessid",
      assets: "Vara",
      catalog: "E-ITS Kataloog",
      mappings: "Vastendused",
      implementationPlan: "Rakenduskava",
      risks: "Riskid",
      evidence: "Tõendid",
      auditView: "Auditi vaade",
      admin: "Admin",
      logout: "Logi välja",
    },
    login: {
      title: "E-ITS Haldussüsteem",
      email: "E-post",
      password: "Parool",
      signIn: "Logi sisse",
      signingIn: "Sisselogimine...",
      invalidCredentials: "Vale e-post või parool",
    },
    dashboard: {
      title: "Töölaud",
      totalMeasures: "Kokku meetmeid",
      implemented: "Rakendatud",
      inProgress: "Töös",
      notStarted: "Alustamata",
      overdueTasks: "Viivitunud ülesanded",
      highRisks: "Kõrged riskid",
      noOverdueTasks: "Viivitunud ülesandeid ei ole",
      noHighRisks: "Kõrgeid riske ei ole",
    },
    businessProcesses: {
      title: "Äriprotsessid",
      noData: "Äriprotsesse veel ei ole.",
    },
    assets: {
      title: "Vara",
      noData: "Vara veel ei ole.",
    },
    catalog: {
      title: "E-ITS Kataloog",
      noData: "Kataloogis andmeid veel ei ole.",
    },
    mappings: {
      title: "Vastendused",
      noData: "Vastendusi veel ei ole.",
    },
    implementationPlan: {
      title: "Rakenduskava",
      noData: "Rakenduskavas objekte veel ei ole.",
    },
    risks: {
      title: "Riskiregister",
      noData: "Riske veel ei ole registreeritud.",
    },
    evidences: {
      title: "Tõendid",
      noData: "Tõendeid veel ei ole üleslaetud.",
    },
    auditView: {
      title: "Auditi vaade",
      noData: "Auditi vaates andmeid ei ole.",
    },
    admin: {
      title: "Admin",
      noData: "Admin paneeli asetus.",
    },
  },
} as const;

export type Language = keyof typeof translations;
export type TranslationKeys = typeof translations.en;