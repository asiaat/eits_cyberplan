import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react"
import { WarningDialog } from "@/components/ui/warning-dialog"
import { setWarningCallback } from "@/lib/warning-dialog"

interface WarningDialogState {
  open: boolean
  title: string
  message: string
}

interface WarningDialogContextType {
  showWarning: (message: string, title?: string) => void
}

const WarningDialogContext = createContext<WarningDialogContextType | null>(null)

export function useWarningDialog() {
  const context = useContext(WarningDialogContext)
  if (!context) {
    throw new Error("useWarningDialog must be used within WarningDialogProvider")
  }
  return context
}

export function WarningDialogProvider({ children }: { children: ReactNode }) {
  const [dialogState, setDialogState] = useState<WarningDialogState>({
    open: false,
    title: "Warning",
    message: "",
  })

  const showWarning = useCallback((message: string, title: string = "Warning") => {
    setDialogState({ open: true, title, message })
  }, [])

  useEffect(() => {
    setWarningCallback(showWarning)
  }, [showWarning])

  const handleOpenChange = (open: boolean) => {
    setDialogState(prev => ({ ...prev, open }))
  }

  return (
    <WarningDialogContext.Provider value={{ showWarning }}>
      {children}
      <WarningDialog
        open={dialogState.open}
        onOpenChange={handleOpenChange}
        title={dialogState.title}
        message={dialogState.message}
      />
    </WarningDialogContext.Provider>
  )
}
