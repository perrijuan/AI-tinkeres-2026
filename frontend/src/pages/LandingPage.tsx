import Navbar from "@/components/landing/Navbar"
import Footer from "@/components/landing/Footer"
import BrandLogo from "@/components/BrandLogo"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  ArrowRight,
  BarChart3,
  HandCoins,
  HeartHandshake,
  Radar,
  ShieldAlert,
  Sprout,
  Users,
  Workflow,
  Wrench,
  Satellite,
  LineChart,
  Building2,
  Tractor,
  Landmark,
  Cloud,
  Droplets,
  Thermometer,
} from "lucide-react"

const painPoints = [
  {
    icon: ShieldAlert,
    title: "Tomada de decisão obsoleta",
    description:
      "O calendário pode dizer que está tudo certo, mas o clima real da área pode apontar risco crescente naquele exato momento.",
  },
  {
    icon: Wrench,
    title: "Tecnologia pouco acessível",
    description:
      "Muitas soluções sustentáveis e avançadas ainda não chegam com simplicidade para pequenos e médios produtores.",
  },
  {
    icon: Workflow,
    title: "Sistemas difíceis de manter",
    description:
      "Ferramentas fragmentadas e pouco intuitivas tornam a leitura de risco lenta, técnica demais e difícil de operacionalizar.",
  },
]

const audiences = [
  {
    icon: Tractor,
    title: "Pequenos e médios produtores",
    description:
      "Precisam entender o risco da safra antes que a perda aconteça e decidir com mais segurança sobre plantio, manejo e monitoramento.",
  },
  {
    icon: Building2,
    title: "Segurados e empresas",
    description:
      "Ganham uma leitura mais clara para priorizar áreas, acompanhar exposição e agir com antecedência diante de anomalias climáticas.",
  },
  {
    icon: Landmark,
    title: "Cooperativas e seguradoras",
    description:
      "Podem complementar a lógica tradicional com dados mais atuais, mais localizados e mais acionáveis por área monitorada.",
  },
]

const solutionPillars = [
  {
    icon: Radar,
    title: "Monitoramento climático em tempo real",
    description:
      "Cruza previsão, sinais recentes e contexto territorial para enxergar risco antes que ele vire dano visível.",
  },
  {
    icon: Satellite,
    title: "Índices de vegetação e solo",
    description:
      "Usa leitura de vegetação, satélite e solo como apoio à decisão, tornando a análise mais contextualizada por área.",
  },
  {
    icon: BarChart3,
    title: "Risco traduzido em ação",
    description:
      "Em vez de só mostrar dado bruto, entrega score, alerta, priorização e recomendação prática para o usuário agir.",
  },
]

const workflowSteps = [
  "Acessa a plataforma",
  "Preenche os dados iniciais",
  "Seleciona a safra",
  "Define a área no mapa",
  "Processa o risco climático",
  "Recebe alertas e recomendações",
]

const odsCards = [
  {
    icon: Sprout,
    title: "ODS 2 — Fome Zero e Agricultura Sustentável",
    description:
      "Fortalece a resiliência da produção de alimentos ao reduzir perdas de safra causadas por risco climático.",
  },
  {
    icon: LineChart,
    title: "ODS 9 — Indústria, Inovação e Infraestrutura",
    description:
      "Moderniza o agronegócio com inovação digital aplicada à leitura de risco e à tomada de decisão.",
  },
  {
    icon: HeartHandshake,
    title: "ODS 17 — Parcerias e Implementação",
    description:
      "Conecta tecnologia de classe mundial, diretrizes governamentais e o setor privado em um ecossistema colaborativo.",
  },
]

const team = [
  { name: "Claudio Almeida", role: "Front End Developer" },
  { name: "Juan Perri (Hamilton)", role: "Data Engineer" },
  { name: "Lucas Rocha", role: "Back End Developer" },
  { name: "Gustavo Felicidade", role: "Business Specialist" },
  { name: "Thais Coffani", role: "Agro Specialist" },
]

const businessNumbers = [
  {
    title: "Operação inicial estimada",
    items: [
      "Earth Engine: US$ 500/mês",
      "Grounding / busca web: US$ 0 dentro do limite gratuito",
      "Gemini com uso moderado: ~US$ 20/mês",
    ],
    emphasis: "Total estimado: US$ 520/mês",
  },
  {
    title: "Receita mensal conservadora",
    items: [
      "10 produtores com ticket médio de R$ 299",
      "1 cooperativa com ticket médio de R$ 3.000",
      "Total bruto estimado: R$ 5.990/mês",
    ],
    emphasis: "Margem estimada: 57%",
  },
]

function SectionTitle({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description: string
}) {
  return (
    <div className="mx-auto mb-14 max-w-3xl text-center">
      <Badge className="mb-4 border-primary/20 bg-primary/10 text-primary">{eyebrow}</Badge>
      <h2 className="text-3xl font-black tracking-tight text-foreground sm:text-4xl">{title}</h2>
      <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">{description}</p>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      <Navbar />

      <main>
        <section className="relative flex min-h-screen items-center overflow-hidden bg-background pt-24 pb-12 text-foreground sm:pt-28 sm:pb-16 lg:pb-0">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(22,163,74,0.16),transparent_32%)] dark:bg-[radial-gradient(circle_at_top,rgba(110,231,183,0.12),transparent_34%)]" />
          <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(2,44,34,0.96)_0%,rgba(6,78,59,0.82)_48%,rgba(15,23,42,0.70)_100%)] dark:bg-[linear-gradient(135deg,rgba(2,6,23,0.92)_0%,rgba(6,78,59,0.58)_48%,rgba(2,44,34,0.74)_100%)]" />
          <div className="absolute inset-0 opacity-[0.06]" style={{
            backgroundImage:
              "repeating-linear-gradient(0deg,transparent,transparent 64px,white 64px,white 65px),repeating-linear-gradient(90deg,transparent,transparent 64px,white 64px,white 65px)",
          }} />

          <div className="relative container mx-auto grid min-h-[calc(100vh-6rem)] max-w-7xl items-center gap-10 px-4 sm:gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-14">
            <div className="min-w-0">
              <div className="mb-5 flex flex-wrap items-center gap-3 sm:mb-6 sm:flex-nowrap">
                <BrandLogo className="h-12 w-12 rounded-[1.2rem] border-white/15 bg-white/95 animate-logo-glow" imageClassName="rounded-[0.95rem]" />
                <Badge className="max-w-full whitespace-normal border-white/15 bg-white/10 py-1.5 text-white">
                  Copiloto climático para proteger a safra antes que o risco vire perda
                </Badge>
              </div>

              <h1 className="max-w-3xl text-4xl font-black leading-[1.04] tracking-tight sm:text-5xl lg:text-6xl">
                SafraViva
                <span className="block text-primary">Cultivando o futuro do agro</span>
              </h1>

              <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/78 sm:mt-6 sm:text-lg">
                A SafraViva é uma plataforma de inteligência agroclimática que ajuda produtores,
                cooperativas e agentes do setor a tomarem decisões melhores diante de seca,
                excesso de chuva e outros eventos extremos.
              </p>

              <div className="mt-7 flex flex-col gap-3 sm:mt-8 sm:flex-row sm:flex-wrap">
                <Button size="lg" className="w-full gap-2 shadow-lg shadow-black/25 sm:w-auto" asChild>
                  <a href="#contato">
                    Solicitar demo
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10 hover:text-white sm:w-auto"
                  asChild
                >
                  <a href="#como-funciona">Ver workflow</a>
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-center py-4 sm:py-8 lg:py-0">
              <div className="relative flex w-full max-w-[34rem] flex-col items-center gap-3 sm:gap-4 lg:min-h-[33rem] lg:items-end lg:justify-center">
                <div className="absolute inset-x-12 bottom-24 h-14 rounded-full bg-primary/25 blur-3xl lg:bottom-4 lg:h-16" />
                <div className="absolute inset-x-3 top-4 h-[18rem] rounded-[2rem] border border-white/10 bg-white/6 shadow-[0_24px_80px_rgba(3,12,8,0.28)] backdrop-blur-[3px] sm:inset-x-8 sm:h-[22rem] lg:inset-x-10 lg:top-8 lg:h-[24rem] lg:rounded-[2.5rem]" />
                <div className="absolute left-2 top-8 h-20 w-20 rounded-full border border-primary/25 bg-primary/12 blur-2xl sm:left-6 sm:top-12 sm:h-24 sm:w-24" />
                <div className="absolute right-2 top-20 h-20 w-20 rounded-full border border-sky-300/20 bg-sky-300/10 blur-2xl sm:right-10 sm:top-28 sm:h-28 sm:w-28 lg:bottom-24 lg:top-auto" />

                <div className="relative z-10 flex w-full items-end justify-center px-4 pt-6 sm:px-6 sm:pt-8">
                  <img
                    src="/agricultor.png"
                    alt="Agricultor representando o produtor rural monitorado pela SafraViva"
                    className="h-[18rem] w-auto object-contain drop-shadow-[0_28px_70px_rgba(0,0,0,0.38)] sm:h-[25rem] lg:h-[33rem]"
                  />
                </div>

                <div className="relative z-20 w-full rounded-[1.25rem] border border-white/16 bg-slate-950/26 p-3 text-white shadow-[0_20px_60px_rgba(2,6,23,0.32)] backdrop-blur-xl sm:max-w-[14rem] sm:self-end sm:p-4 lg:absolute lg:right-1 lg:top-28 lg:w-44 lg:rounded-[1.5rem]">
                  <p className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-white/58">
                    <Cloud className="h-3.5 w-3.5 text-sky-200" />
                    Clima agora
                  </p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-black leading-none sm:text-3xl">28°C</span>
                    <span className="pb-1 text-[11px] text-white/55">tempo estável</span>
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-xs text-white/68">
                    <Droplets className="h-3.5 w-3.5 text-sky-200" />
                    Umidade de 72%
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-white/55">
                    <Thermometer className="h-3.5 w-3.5 text-orange-200" />
                    12 mm previstos na semana
                  </div>
                </div>

                <div className="relative z-20 w-full rounded-[1.25rem] border border-white/14 bg-white/10 px-4 py-3 text-white shadow-[0_18px_50px_rgba(2,6,23,0.28)] backdrop-blur-xl sm:max-w-[18rem] lg:absolute lg:bottom-12 lg:right-8 lg:w-auto lg:rounded-[1.35rem]">
                  <p className="text-[11px] uppercase tracking-[0.24em] text-white/55">Leitura contínua</p>
                  <p className="mt-1 text-sm font-semibold text-white/88">Satélite + clima + ZARC trabalhando juntos</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="mercado" className="bg-muted/35 py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="Problemas de Mercado"
              title="O mercado já sente o peso do risco climático"
              description="As perdas crescem, a cobertura ainda é baixa e a tomada de decisão continua lenta em muitos fluxos operacionais do agro."
            />

            <div className="grid gap-6 md:grid-cols-3">
              {painPoints.map((item) => (
                <Card key={item.title} className="border-2 border-border bg-card">
                  <CardHeader>
                    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm leading-relaxed text-muted-foreground">
                    {item.description}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="para-quem" className="py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="Público Alvo"
              title="Para quem a SafraViva gera valor"
              description="A proposta é servir quem precisa decidir com mais segurança e menos atraso diante da variabilidade climática."
            />

            <div className="grid gap-6 md:grid-cols-3">
              {audiences.map((item) => (
                <Card key={item.title}>
                  <CardHeader>
                    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm leading-relaxed text-muted-foreground">
                    {item.description}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="solucao" className="bg-[linear-gradient(180deg,rgba(22,163,74,0.04)_0%,rgba(22,163,74,0.08)_100%)] dark:bg-[linear-gradient(180deg,rgba(16,185,129,0.05)_0%,rgba(15,23,42,0.02)_100%)] py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="SafraViva"
              title="Uma plataforma para transformar risco climático em decisão"
              description="A solução combina monitoramento climático em tempo real, leitura de vegetação e solo e uma camada de interpretação prática para o usuário agir antes da perda."
            />

            <div className="grid gap-6 lg:grid-cols-3">
              {solutionPillars.map((item) => (
                <Card key={item.title} className="border-primary/15">
                  <CardHeader>
                    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm leading-relaxed text-muted-foreground">
                    {item.description}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="como-funciona" className="py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="Workflow"
              title="Como a experiência funciona na prática"
              description="Do acesso à plataforma até os alertas e recomendações, o fluxo foi pensado para ser simples, visual e orientado à ação."
            />

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
              {workflowSteps.map((step, index) => (
                <Card key={step} className="relative overflow-visible border-border bg-card">
                  <CardContent className="p-5">
                    <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                      {index + 1}
                    </div>
                    <p className="text-sm font-semibold leading-snug text-foreground">{step}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="impacto" className="bg-foreground py-24 text-background">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="ODS"
              title="Impacto alinhado a desenvolvimento sustentável"
              description="A SafraViva contribui para resiliência produtiva, inovação aplicada ao agro e construção de um ecossistema mais conectado."
            />

            <div className="grid gap-6 md:grid-cols-3">
              {odsCards.map((item) => (
                <Card key={item.title} className="border-background/10 bg-background/5 text-background">
                  <CardHeader>
                    <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-background/10 text-primary">
                      <item.icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm leading-relaxed text-background/72">
                    {item.description}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="Modelo de Negócio"
              title="Estrutura enxuta e viabilidade inicial"
              description="O pitch já aponta um cenário conservador de operação com custo controlado e espaço para margem positiva desde os primeiros contratos."
            />

            <div className="grid gap-6 lg:grid-cols-2">
              {businessNumbers.map((block) => (
                <Card key={block.title}>
                  <CardHeader>
                    <CardTitle className="text-xl">{block.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm text-muted-foreground">
                      {block.items.map((item) => (
                        <div key={item} className="flex gap-3">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                    <Separator className="my-5" />
                    <div className="flex items-center gap-3 rounded-2xl border border-primary/15 bg-primary/5 p-4">
                      <HandCoins className="h-5 w-5 text-primary" />
                      <p className="text-sm font-semibold text-foreground">{block.emphasis}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-muted/35 py-24">
          <div className="container mx-auto max-w-7xl px-4">
            <SectionTitle
              eyebrow="Time"
              title="Equipe por trás do projeto"
              description="Uma composição multidisciplinar com frente técnica, dados, negócio e conhecimento do agro."
            />

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {team.map((member) => (
                <Card key={member.name} className="border-border bg-card">
                  <CardContent className="p-5">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Users className="h-5 w-5" />
                    </div>
                    <p className="text-sm font-semibold text-foreground">{member.name}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{member.role}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="contato" className="py-24">
          <div className="container mx-auto max-w-5xl px-4">
            <Card className="overflow-hidden border-primary/15 bg-[linear-gradient(135deg,rgba(22,163,74,0.08)_0%,rgba(255,255,255,0.96)_100%)] dark:bg-[linear-gradient(135deg,rgba(22,163,74,0.10)_0%,rgba(15,23,42,0.92)_100%)]">
              <CardContent className="grid gap-10 p-8 md:grid-cols-[1fr_auto] md:items-center">
                <div>
                  <Badge className="mb-4 border-primary/20 bg-primary/10 text-primary">Muito obrigado</Badge>
                  <h2 className="text-3xl font-black tracking-tight text-foreground sm:text-4xl">
                    Proteja a safra antes que o risco vire perda
                  </h2>
                  <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground">
                    Se a ideia faz sentido para seu contexto, o próximo passo é simples:
                    ver o fluxo na prática e entender como a SafraViva pode apoiar decisão,
                    monitoramento e priorização de risco.
                  </p>
                </div>

                <div className="flex flex-col gap-3">
                  <Button size="lg" className="gap-2" asChild>
                    <a href="/solicitar-demo">
                      Ir para a demo
                      <ArrowRight className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button size="lg" variant="outline" asChild>
                    <a href="#mercado">Voltar ao problema</a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
