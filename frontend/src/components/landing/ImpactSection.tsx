import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { Leaf, Cloud, Users } from "lucide-react"

const sdgs = [
  {
    number: "ODS 2",
    title: "Agricultura Sustentável",
    description:
      "Contribuímos para acabar com a fome, alcançar segurança alimentar e promover a agricultura sustentável.",
    detail:
      "Ao reduzir perdas agrícolas com informação de risco mais precisa, contribuímos para maior eficiência na produção de alimentos e menor desperdício de insumos.",
    icon: Leaf,
    /* ODS 2 usa primary — verde = agricultura = marca SafraViva */
    iconCls: "text-primary",
    iconBg: "bg-primary/10",
    border: "border-primary/20",
    badgeCls: "bg-primary/10 text-primary border-0",
  },
  {
    number: "ODS 13",
    title: "Ação Climática",
    description:
      "Fortalecemos a resiliência e a capacidade de adaptação a riscos relacionados ao clima e às mudanças climáticas.",
    detail:
      "Ferramentas de inteligência climática permitem que agricultores e seguradoras se adaptem melhor às mudanças climáticas em curso e antecipem eventos extremos.",
    icon: Cloud,
    /* Azul mantido para diferenciar os três ODS */
    iconCls: "text-blue-600 dark:text-blue-400",
    iconBg: "bg-blue-50 dark:bg-blue-900/20",
    border: "border-blue-200 dark:border-blue-700",
    badgeCls: "bg-blue-100 text-blue-700 border-0 dark:bg-blue-900/30 dark:text-blue-300",
  },
  {
    number: "ODS 17",
    title: "Parcerias",
    description:
      "Fortalecemos parcerias globais para o desenvolvimento sustentável, conectando diferentes atores do agronegócio.",
    detail:
      "A SafraViva conecta seguradoras, cooperativas, produtores e governo em um ecossistema de dados compartilhados — fortalecendo as parcerias necessárias para um agro mais resiliente.",
    icon: Users,
    /* Roxo mantido para diferenciar os três ODS */
    iconCls: "text-purple-600 dark:text-purple-400",
    iconBg: "bg-purple-50 dark:bg-purple-900/20",
    border: "border-purple-200 dark:border-purple-700",
    badgeCls: "bg-purple-100 text-purple-700 border-0 dark:bg-purple-900/30 dark:text-purple-300",
  },
]

export default function ImpactSection() {
  return (
    <section id="impacto" className="py-24 bg-muted/40">
      <div className="container mx-auto max-w-7xl px-4">
        <div className="text-center space-y-4 mb-14">
          {/* bg-primary/10 text-primary — reactivo ao tema */}
          <Badge className="bg-primary/10 text-primary border border-primary/20 text-xs">
            Impacto & ODS
          </Badge>
          <h2 className="text-4xl font-bold tracking-tight">
            Resultado econômico com propósito global
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            Menos perdas no campo significa mais segurança alimentar, mais
            resiliência climática e mais parcerias sustentáveis. A SafraViva
            alinha lucro e impacto — contribuindo diretamente para três ODS da ONU.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-14">
          {sdgs.map((sdg) => (
            <HoverCard key={sdg.number} openDelay={150} closeDelay={100}>
              <HoverCardTrigger asChild>
                <Card
                  className={`border-2 ${sdg.border} cursor-default hover:shadow-md transition-shadow bg-card`}
                >
                  <CardContent className="p-8 text-center space-y-4">
                    <div
                      className={`w-14 h-14 ${sdg.iconBg} border ${sdg.border} rounded-2xl flex items-center justify-center mx-auto`}
                    >
                      <sdg.icon className={`w-7 h-7 ${sdg.iconCls}`} />
                    </div>
                    <Badge className={sdg.badgeCls}>{sdg.number}</Badge>
                    <div>
                      <h3 className="font-bold text-lg mb-2">{sdg.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {sdg.description}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </HoverCardTrigger>
              <HoverCardContent className="w-72" side="bottom">
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {sdg.detail}
                </p>
              </HoverCardContent>
            </HoverCard>
          ))}
        </div>

        <Separator className="mb-14" />

        <div className="grid md:grid-cols-2 gap-10 items-center">
          <div className="space-y-4">
            <h3 className="text-2xl font-bold">Nossa Visão</h3>
            <p className="text-muted-foreground leading-relaxed">
              Ser uma das principais referências em inteligência de risco
              climático para o agro na América Latina — tornando o campo mais
              resiliente, eficiente e sustentável.
            </p>
          </div>
          <div className="space-y-4">
            <h3 className="text-2xl font-bold">Nossa Missão</h3>
            <p className="text-muted-foreground leading-relaxed">
              Ajudar o agronegócio a tomar decisões mais seguras usando dados —
              complementando os modelos regulatórios com inteligência em tempo
              real.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
