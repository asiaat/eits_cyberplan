// OVERRIDE window.alert BEFORE ANYTHING ELSE
const originalAlert = window.alert;
window.alert = function(...args) {
  const message = args[0];
  if (typeof message === 'string' && message) {
    // Create custom modal directly
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:999999;font-family:system-ui,sans-serif;';
    
    const modal = document.createElement('div');
    modal.style.cssText = 'background:white;border-radius:12px;padding:24px;max-width:420px;width:90%;box-shadow:0 25px 50px -12px rgba(0,0,0,0.25);';
    
    const header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;gap:12px;margin-bottom:16px;';
    
    const icon = document.createElement('div');
    icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y1="17"/></svg>';
    
    const title = document.createElement('h3');
    title.textContent = 'Warning';
    title.style.cssText = 'margin:0;font-size:18px;font-weight:600;color:#1f2937;';
    
    const body = document.createElement('div');
    body.textContent = message;
    body.style.cssText = 'color:#6b7280;font-size:14px;line-height:1.5;margin-bottom:24px;word-break:break-word;';
    
    const btn = document.createElement('button');
    btn.textContent = 'OK';
    btn.style.cssText = 'width:100%;padding:10px 16px;background:#3b82f6;color:white;border:none;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;';
    btn.onclick = () => document.body.removeChild(overlay);
    
    header.appendChild(icon);
    header.appendChild(title);
    modal.appendChild(header);
    modal.appendChild(body);
    modal.appendChild(btn);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    overlay.onclick = (e) => { if (e.target === overlay) document.body.removeChild(overlay); };
    return;
  }
  return originalAlert.apply(window, args);
};

import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import "./index.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
