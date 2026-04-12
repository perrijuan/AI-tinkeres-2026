import { Badge } from "@/components/ui/badge"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    q: "O SafraViva substitui o ZARC?",
    a: "Não. O SafraViva complementa o ZARC com dados satelitais e climáticos em tempo real. O ZARC define janelas de plantio baseadas em séries históricas longas — o SafraViva enriquece essa base com o que está acontecendo agora na sua área específica, gerando um score atualizado por talhão.",
  },
  {
    q: "Como o score de risco é calculado?",
    a: "O algoritmo cruza quatro fontes: a janela ZARC da cultura e município, dados climáticos dos últimos 7 dias e previsão de 14 dias (NOAA/GFS via Google Earth Engine), índices de vegetação por satélite (MODIS e Sentinel-2) e contexto produtivo local. O resultado é um score de 0 a 100 com nível de risco e alertas acionáveis.",
  },
  {
    q: "Quais culturas são suportadas?",
    a: "Soja, milho e algodão têm perfis agronômicos completos com thresholds calibrados individualmente. O motor também processa outras culturas com perfil padrão. A cobertura está sendo ampliada continuamente.",
  },
  {
    q: "Preciso de equipamento especial ou acesso a satélites?",
    a: "Não. Basta desenhar o talhão no mapa da plataforma. A coleta de dados via satélite é feita automaticamente pelo sistema — sem hardware adicional, sem instalação, sem configuração técnica.",
  },
  {
    q: "O SafraViva funciona em qualquer região do Brasil?",
    a: "O motor de análise funciona para qualquer polígono desenhado — qualquer área gera score. A cobertura completa do ZARC local prioriza Mato Grosso hoje e está em expansão para todo o território nacional.",
  },
  {
    q: "Como integro ao meu sistema existente?",
    a: "Para seguradoras e cooperativas, disponibilizamos API REST para integração direta. Para produtores e pequenas operações, a plataforma web já funciona sem nenhuma instalação. White-label e SLA por contrato disponíveis para parceiros enterprise.",
  },
  {
    q: "Com que frequência os dados climáticos são atualizados?",
    a: "A fonte primária é o NOAA/GFS via Google Earth Engine, com ciclos de atualização de 3 a 6 horas. A cada nova rodada de dados, o score da área é recalculado automaticamente — sem necessidade de ação do usuário.",
  },
  {
    q: "Como o SafraViva se relaciona com os ODS da ONU?",
    a: "O SafraViva contribui diretamente para três objetivos: ODS 2 (Fome Zero e Agricultura Sustentável), ao reduzir perdas com informação de risco mais precisa; ODS 13 (Ação Climática), ao fortalecer a resiliência do campo frente às mudanças climáticas; e ODS 17 (Parcerias), ao conectar seguradoras, cooperativas, produtores e governo em um ecossistema de dados compartilhados.",
  },
]

export default function FAQSection() {
  return (
    <section id="faq" className="py-24 bg-background">
      <div className="container mx-auto max-w-3xl px-4">
        <div className="text-center space-y-4 mb-12">
          <Badge variant="outline" className="text-xs">
            Perguntas Frequentes
          </Badge>
          <h2 className="text-4xl font-bold tracking-tight">
            Dúvidas comuns
          </h2>
          <p className="text-muted-foreground text-lg leading-relaxed">
            Tudo o que você precisa saber antes de começar.
          </p>
        </div>

        <Accordion type="single" collapsible className="space-y-2">
          {faqs.map((faq, i) => (
            <AccordionItem
              key={i}
              value={`item-${i}`}
              className="border rounded-xl px-6 data-[state=open]:border-primary/30 transition-colors"
            >
              <AccordionTrigger className="text-left text-sm font-semibold hover:no-underline py-5">
                {faq.q}
              </AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground leading-relaxed pb-5">
                {faq.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  )
}
