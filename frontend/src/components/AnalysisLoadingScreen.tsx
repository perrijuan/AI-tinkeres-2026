import { useEffect, useState } from "react"
import { Bot, Sparkles } from "lucide-react"

import BrandLogo from "@/components/BrandLogo"

const DEFAULT_MESSAGES = [
  "Validando o recorte do talhão e organizando a geometria da área…",
  "Buscando sinais climáticos recentes e projetando os próximos dias…",
  "Analisando indicadores de satélite para entender o vigor da vegetação…",
  "Conferindo aderência ao ZARC e ao contexto agronômico da cultura…",
  "Calculando risco, priorizando alertas e preparando a leitura da Safrinia…",
  "Montando gráficos, tabelas e recomendações para o dashboard final…",
]

type AnalysisLoadingScreenProps = {
  title?: string
  subtitle?: string
  messages?: string[]
}

export default function AnalysisLoadingScreen({
  title = "Gerando seu dashboard agroclimático",
  subtitle = "Estamos cruzando clima, satélite, território e contexto agronômico para montar uma leitura mais clara da sua área.",
  messages = DEFAULT_MESSAGES,
}: AnalysisLoadingScreenProps) {
  const [loadingStep, setLoadingStep] = useState(0)
  const [typedText, setTypedText] = useState("")

  useEffect(() => {
    const interval = window.setInterval(() => {
      setLoadingStep((prev) => (prev + 1) % messages.length)
    }, 1400)

    return () => window.clearInterval(interval)
  }, [messages])

  useEffect(() => {
    const target = messages[loadingStep]
    let index = 0
    setTypedText("")

    const typing = window.setInterval(() => {
      index += 1
      setTypedText(target.slice(0, index))
      if (index >= target.length) {
        window.clearInterval(typing)
      }
    }, 24)

    return () => window.clearInterval(typing)
  }, [loadingStep, messages])

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(22,163,74,0.14),transparent_34%)] dark:bg-[radial-gradient(circle_at_top,rgba(110,231,183,0.12),transparent_30%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.86)_0%,rgba(244,248,244,0.96)_100%)] dark:bg-[linear-gradient(180deg,rgba(2,6,23,0.92)_0%,rgba(3,14,10,0.96)_100%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.05] dark:opacity-[0.06]" style={{
        backgroundImage:
          "repeating-linear-gradient(0deg,transparent,transparent 72px,currentColor 72px,currentColor 73px),repeating-linear-gradient(90deg,transparent,transparent 72px,currentColor 72px,currentColor 73px)",
      }} />
      <div className="mx-auto flex min-h-screen max-w-4xl items-center justify-center px-6">
        <div className="relative flex w-full flex-col items-center text-center">
          <div className="relative mb-8 flex items-center justify-center">
            <div className="absolute h-32 w-32 rounded-full bg-primary/12 blur-3xl dark:bg-primary/20" />
            <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-border/70 bg-card/90 shadow-[0_18px_40px_rgba(15,23,42,0.10)] backdrop-blur dark:border-white/10 dark:bg-card/80 dark:shadow-[0_22px_52px_rgba(0,0,0,0.45)]">
              <div className="absolute h-20 w-20 animate-spin rounded-full border-2 border-primary/15 border-t-primary dark:border-primary/20" />
              <div className="absolute -right-2 -top-2 rounded-2xl bg-primary p-2 text-primary-foreground shadow-md animate-[bounce_1.8s_ease-in-out_infinite] dark:shadow-[0_10px_24px_rgba(16,185,129,0.28)]">
                <Bot className="h-4 w-4" />
              </div>
              <BrandLogo className="h-12 w-12 rounded-[1.1rem] p-1 shadow-md" imageClassName="rounded-[0.9rem]" />
            </div>
          </div>

          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/80 px-4 py-2 text-xs font-medium text-primary shadow-sm backdrop-blur dark:border-white/10 dark:bg-card/70">
            <Sparkles className="h-3.5 w-3.5" />
            Safrinia preparando sua leitura da área
          </div>

          <h1 className="max-w-2xl text-3xl font-black tracking-tight text-foreground sm:text-4xl">
            {title}
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            {subtitle}
          </p>

          <div className="mt-8 min-h-16 max-w-2xl rounded-2xl border border-border/70 bg-card/85 px-5 py-4 text-sm text-foreground shadow-[0_12px_32px_rgba(15,23,42,0.08)] backdrop-blur dark:border-white/10 dark:bg-card/75 dark:shadow-[0_20px_48px_rgba(0,0,0,0.32)] sm:text-base">
            <span>{typedText}</span>
            <span className="ml-1 inline-block h-5 w-[2px] animate-pulse bg-primary align-middle" />
          </div>

          <div className="mt-6 h-1.5 w-full max-w-md overflow-hidden rounded-full bg-muted dark:bg-white/10">
            <div
              className="h-full rounded-full bg-primary shadow-[0_0_18px_rgba(16,185,129,0.22)] transition-all duration-500 dark:shadow-[0_0_24px_rgba(110,231,183,0.30)]"
              style={{ width: `${((loadingStep + 1) / messages.length) * 100}%` }}
            />
          </div>

          <p className="mt-4 text-xs text-muted-foreground">
            Isso leva só alguns segundos.
          </p>
        </div>
      </div>
    </div>
  )
}
