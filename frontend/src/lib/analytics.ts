/**
 * Camada de rastreamento Google Analytics 4.
 *
 * Nomenclatura de eventos:
 *   funnel_step_view      – usuário entra em um passo do funil de demo
 *   funnel_step_complete  – usuário avança de passo (clica "Próximo")
 *   demo_submitted        – análise enviada com sucesso para o backend
 *   cultura_selected      – cultura escolhida no passo 2
 *   cta_click             – qualquer clique em botão CTA primário
 *   nav_click             – link de navegação da Navbar
 *   email_signup          – formulário de e-mail na seção de contato
 *   chat_opened           – chat Safrinia aberto
 *   chat_closed           – chat Safrinia fechado
 *   chat_message_sent     – mensagem enviada ao assistente
 */

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void
    dataLayer?: unknown[]
  }
}

type EventParams = Record<string, string | number | boolean | undefined>

function track(eventName: string, params?: EventParams) {
  try {
    if (typeof window !== "undefined" && typeof window.gtag === "function") {
      window.gtag("event", eventName, params)
    }
  } catch {
    // Nunca deixar erro de analytics quebrar a experiência
  }
}

// ── Funil de demo ─────────────────────────────────────────────────────────────

/** Dispara quando o usuário visualiza um passo do wizard de demo. */
export function trackFunnelStepView(step: number, stepName: string) {
  track("funnel_step_view", {
    funnel_name: "demo_request",
    step_number: step,
    step_name: stepName,
  })
}

/** Dispara quando o usuário completa um passo e avança. */
export function trackFunnelStepComplete(
  step: number,
  stepName: string,
  extra?: EventParams
) {
  track("funnel_step_complete", {
    funnel_name: "demo_request",
    step_number: step,
    step_name: stepName,
    ...extra,
  })
}

/** Dispara quando a análise é submetida ao backend. */
export function trackDemoSubmitted(cultura: string, areaHa: number) {
  track("demo_submitted", {
    funnel_name: "demo_request",
    culture: cultura,
    area_ha: Math.round(areaHa * 10) / 10,
  })
}

/** Dispara quando o usuário seleciona uma cultura no passo 2. */
export function trackCulturaSelected(culturaId: string, culturaLabel: string) {
  track("cultura_selected", {
    cultura_id: culturaId,
    cultura_label: culturaLabel,
  })
}

// ── CTAs e navegação ──────────────────────────────────────────────────────────

/** Dispara em cliques de botões CTA primários. */
export function trackCTAClick(
  buttonId: string,
  buttonText: string,
  destination?: string
) {
  track("cta_click", {
    button_id: buttonId,
    button_text: buttonText,
    destination,
  })
}

/** Dispara em cliques nos links da Navbar. */
export function trackNavClick(label: string, href: string) {
  track("nav_click", {
    link_text: label,
    link_url: href,
  })
}

/** Dispara quando o formulário de e-mail da seção de contato é enviado. */
export function trackEmailSignup(section: string) {
  track("email_signup", { section })
}

// ── Chat Safrinia ─────────────────────────────────────────────────────────────

export function trackChatOpened() {
  track("chat_opened", { chat_name: "safrinia" })
}

export function trackChatClosed() {
  track("chat_closed", { chat_name: "safrinia" })
}

/** messageIndex começa em 1 — representa a mensagem que está sendo enviada. */
export function trackChatMessageSent(messageIndex: number) {
  track("chat_message_sent", {
    chat_name: "safrinia",
    message_index: messageIndex,
  })
}
