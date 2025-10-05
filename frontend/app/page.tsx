import DigitalClock from "./components/DigitalClock"
import DeployedApps from "./components/DeployedApps"

export default function Home() {
  return (
    <main data-theme="purple" className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 flex flex-col min-h-screen">
        {/* Header section with clock */}
        <div className="flex flex-col items-center justify-center py-12">
          <h1 className="text-5xl font-medium text-primary/90 font-['Space_Mono'] mb-4">(lambda-gateway)</h1>
          <DigitalClock />
        </div>

        {/* Main content area */}
        <div className="flex-1 flex items-start justify-center py-8">
          <DeployedApps />
        </div>
      </div>
    </main>
  )
}
