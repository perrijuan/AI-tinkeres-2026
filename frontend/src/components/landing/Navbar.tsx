import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Menu } from "lucide-react"
import { cn } from "@/lib/utils"

const navLinks = [
  { href: "#problema", label: "Problema" },
  { href: "#solucao", label: "Solução" },
  { href: "#como-funciona", label: "Como Funciona" },
  { href: "#para-quem", label: "Para Quem" },
  { href: "#mercado", label: "Mercado" },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener("scroll", handler)
    return () => window.removeEventListener("scroll", handler)
  }, [])

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-background/95 backdrop-blur-md border-b shadow-sm"
          : "bg-transparent"
      )}
    >
      <nav className="container mx-auto max-w-7xl px-4 h-16 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2.5">
          <img
            src="/logo.jpeg"
            alt="Logo SafraViva"
            className="h-8 w-8 shrink-0 rounded-lg object-cover"
          />
          <div className="leading-none">
            <span
              className={cn(
                "font-bold text-base block transition-colors",
                scrolled ? "text-foreground" : "text-white"
              )}
            >
              SafraViva
            </span>
            <span
              className={cn(
                "text-[10px] block transition-colors",
                scrolled ? "text-muted-foreground" : "text-white/60"
              )}
            >
              Inteligência Climática
            </span>
          </div>
        </a>

        <div className="hidden md:flex items-center">
          <NavigationMenu>
            <NavigationMenuList>
              {navLinks.map((link) => (
                <NavigationMenuItem key={link.href}>
                  <NavigationMenuLink
                    href={link.href}
                    className={cn(
                      navigationMenuTriggerStyle(),
                      !scrolled &&
                        "bg-transparent text-white/90 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    {link.label}
                  </NavigationMenuLink>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        <div className="flex items-center gap-2">
          <Button className="hidden md:flex" asChild>
            <Link to="/solicitar-demo">Solicitar Demo</Link>
          </Button>

          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "md:hidden",
                  !scrolled && "text-white hover:bg-white/10 hover:text-white"
                )}
              >
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <div className="flex items-center gap-2.5 mb-6 mt-2">
                <img
                  src="/logo.jpeg"
                  alt="Logo SafraViva"
                  className="h-8 w-8 rounded-lg object-cover"
                />
                <span className="font-bold text-base">SafraViva</span>
              </div>
              <Separator className="mb-4" />
              <div className="flex flex-col gap-1">
                {navLinks.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setOpen(false)}
                    className="px-3 py-2.5 rounded-md text-sm hover:bg-accent transition-colors font-medium"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
              <Separator className="my-4" />
              <Button className="w-full" asChild>
                <Link to="/solicitar-demo">Solicitar Demo</Link>
              </Button>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  )
}
