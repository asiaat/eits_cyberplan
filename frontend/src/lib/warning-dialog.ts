type WarningCallback = (message: string, title?: string) => void

let warningCallback: WarningCallback | null = null
const messageQueue: Array<{ message: string; title?: string }> = []

export function setWarningCallback(callback: WarningCallback) {
  warningCallback = callback
  while (messageQueue.length > 0) {
    const msg = messageQueue.shift()
    if (msg) callback(msg.message, msg.title)
  }
}

export function showWarningDialog(message: string, title: string = "Warning") {
  if (warningCallback) {
    warningCallback(message, title)
  } else {
    messageQueue.push({ message, title })
  }
}

function createNativeStyleModal(message: string, title: string) {
  const overlay = document.createElement("div")
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999999;
    font-family: system-ui, -apple-system, sans-serif;
  `

  const modal = document.createElement("div")
  modal.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 24px;
    max-width: 420px;
    width: 90%;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  `

  const header = document.createElement("div")
  header.style.cssText = `
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  `

  const icon = document.createElement("div")
  icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>`
  icon.style.cssText = `flex-shrink: 0;`

  const titleEl = document.createElement("h3")
  titleEl.textContent = title
  titleEl.style.cssText = `
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  `

  const body = document.createElement("div")
  body.style.cssText = `
    color: #6b7280;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 24px;
    word-break: break-word;
  `
  body.textContent = message

  const button = document.createElement("button")
  button.textContent = "OK"
  button.style.cssText = `
    width: 100%;
    padding: 10px 16px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  `
  button.onmouseover = () => button.style.background = "#2563eb"
  button.onmouseout = () => button.style.background = "#3b82f6"
  button.onclick = () => {
    document.body.removeChild(overlay)
  }

  header.appendChild(icon)
  header.appendChild(titleEl)
  modal.appendChild(header)
  modal.appendChild(body)
  modal.appendChild(button)
  overlay.appendChild(modal)
  document.body.appendChild(overlay)

  overlay.onclick = (e) => {
    if (e.target === overlay) {
      document.body.removeChild(overlay)
    }
  }
}

export function interceptNativeAlerts() {
  const origAlert = window.alert
  
  window.alert = function (...args: unknown[]) {
    const message = args[0]
    if (typeof message === "string" && message.trim()) {
      createNativeStyleModal(message, "Warning")
      return
    }
    if (args.length > 1 && typeof args[1] === "string") {
      createNativeStyleModal(args[1], typeof args[0] === "string" ? args[0] : "Warning")
      return
    }
    return origAlert.apply(window, args as [any])
  }
}
