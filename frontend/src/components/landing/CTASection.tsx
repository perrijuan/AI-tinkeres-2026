import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ArrowRight, CheckCircle2 } from "lucide-react"
import { trackEmailSignup } from "@/lib/analytics"

export default function CTASection() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (email) {
      trackEmailSignup("cta_section")
      setSubmitted(true)
    }
  }

  return (
    <section className="py-24 bg-linear-to-br from-green-950 via-emerald-900 to-teal-900 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-primary/8 rounded-full blur-3xl" />
      </div>

      <div className="relative container mx-auto max-w-4xl px-4 text-center space-y-10 text-white">
        <div className="space-y-6">
          <Badge className="bg-primary/25 text-primary-foreground/85 border border-primary/40 text-xs">
            Próximos Passos
          </Badge>
          <h2 className="text-4xl lg:text-5xl font-bold tracking-tight leading-[1.1]">
            Pronto para tomar decisões com mais{" "}
            {/* text-primary — emerald-600 light / emerald-400 dark, reactivo ao tema */}
            <span className="text-primary">inteligência?</span>
          </h2>
          <p className="text-primary-foreground/65 text-lg max-w-2xl mx-auto leading-relaxed">
            O foco agora está em validar a solução em campo com parceiros
            estratégicos. Entre em contato para saber como a SafraViva pode
            complementar a sua operação.
          </p>
        </div>

        <Card className="bg-white/8 backdrop-blur-md border-white/15 max-w-md mx-auto shadow-2xl">
          <CardContent className="p-6 space-y-4">
            {submitted ? (
              <Alert className="border-primary/30 bg-primary/10 text-white">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <AlertDescription className="text-primary-foreground/80 text-sm">
                  Recebemos seu contato! Entraremos em contato em até 24 horas.
                </AlertDescription>
              </Alert>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3">
                <p className="text-white/70 text-sm text-left">
                  Solicite uma demonstração gratuita
                </p>
                <div className="flex gap-2">
                  <Input
                    id="input-cta-email"
                    type="email"
                    placeholder="seu@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-white/10 border-white/20 text-white placeholder:text-white/40 focus:border-primary flex-1"
                    required
                  />
                  <Button
                    id="btn-cta-email-enviar"
                    type="submit"
                    className="gap-1.5 shrink-0"
                    size="sm"
                  >
                    Enviar
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
                <p className="text-[11px] text-white/40 text-left">
                  Sem compromisso. Entraremos em contato em até 24 horas.
                </p>
              </form>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-center gap-8 text-sm text-primary-foreground/55 flex-wrap">
          {[
            "Parcerias com seguradoras",
            "Testes com cooperativas",
            "Integração com instituições financeiras",
          ].map((item) => (
            <span key={item} className="flex items-center gap-2">
              {/* bg-primary reactivo ao tema */}
              <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block" />
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
