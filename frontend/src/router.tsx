import { createBrowserRouter } from "react-router-dom"
import LandingPage from "@/pages/LandingPage"
import DemoPage from "@/pages/DemoPage"
import ResultsPage from "@/pages/ResultsPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    path: "/solicitar-demo",
    element: <DemoPage />,
  },
  {
    path: "/resultado",
    element: <ResultsPage />,
  },
])
