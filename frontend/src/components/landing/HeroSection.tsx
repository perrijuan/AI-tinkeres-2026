import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { ArrowRight, ChevronDown, Radio, TrendingUp, Shield } from "lucide-react"

const FIELD_IMAGE =
  "https://images.pexels.com/photos/7728939/pexels-photo-7728939.jpeg"

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-linear-to-br from-green-950 via-emerald-900 to-teal-900">
      {/* Blobs decorativos */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-20 left-10 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-primary/8 rounded-full blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg,transparent,transparent 60px,white 60px,white 61px),repeating-linear-gradient(90deg,transparent,transparent 60px,white 60px,white 61px)",
          }}
        />
      </div>

      <div className="relative container mx-auto max-w-7xl px-4 py-32 grid lg:grid-cols-2 gap-16 items-center">

        {/* ── Coluna esquerda: copy ── */}
        <div className="text-white space-y-8">
          <Badge className="bg-primary/25 text-primary-foreground/85 border border-primary/40 text-xs px-3 py-1 w-fit">
            🛰️ Score de risco climático em tempo real
          </Badge>

          <div className="space-y-5">
            <h1 className="text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight">
              Decisões mais{" "}
              <span className="text-primary">seguras</span>{" "}
              para a agricultura brasileira
            </h1>
            <p className="text-lg text-primary-foreground/70 leading-relaxed max-w-lg">
              O SafraViva integra o ZARC com dados satelitais em tempo real,
              gerando scores de risco precisos por área agrícola — atualizado
              continuamente para refletir o que acontece agora.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button size="lg" className="gap-2 shadow-lg shadow-black/30">
              Solicitar Demo Gratuita
              <ArrowRight className="w-4 h-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/25 text-white hover:bg-white/10 hover:text-white"
              asChild
            >
              <a href="#como-funciona">Como Funciona</a>
            </Button>
          </div>

          <div className="flex items-center gap-5 pt-1 flex-wrap">
            {[
              { icon: Shield, label: "Complementa o ZARC" },
              { icon: Radio, label: "Sentinel + MODIS" },
              { icon: TrendingUp, label: "Cobertura nacional" },
            ].map((item, i) => (
              <span key={item.label} className="flex items-center gap-5">
                {i > 0 && (
                  <Separator
                    orientation="vertical"
                    className="h-3.5 bg-primary/40"
                  />
                )}
                <span className="flex items-center gap-1.5 text-primary-foreground/60 text-sm">
                  <item.icon className="w-3.5 h-3.5" />
                  {item.label}
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* ── Coluna direita: só a imagem ── */}
        <div className="hidden lg:flex items-center justify-center">
          <div className="rounded-2xl overflow-hidden shadow-2xl w-full aspect-4/3">
            <img
              src={FIELD_IMAGE}
              alt="Área agrícola monitorada por satélite"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </div>

      <a
        href="#problema"
        className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/40 animate-bounce hover:text-white/70 transition-colors"
      >
        <ChevronDown className="w-6 h-6" />
      </a>
    </section>
  )
}
