"use client"

import { useState, useEffect } from "react"
import { Plus, ExternalLink } from "lucide-react"
import BuildModal from "./BuildModal"

interface DeployedApp {
  app_name: string
  url: string
  port: number
  framework: string
  env_vars: Record<string, string>
}

const backend_url = process.env.NEXT_PUBLIC_BACKEND_URL

console.log("[v0] Backend URL:", backend_url)

export default function DeployedApps() {
  const [apps, setApps] = useState<DeployedApp[]>([])
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const fetchApps = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${backend_url}/apps`)
      const data = await response.json()
      setApps(data.apps || [])
    } catch (error) {
      console.error("[v0] Error fetching apps:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchApps()
  }, [])

  const handleBuildSuccess = () => {
    fetchApps()
    setIsModalOpen(false)
  }

  return (
    <div className="flex flex-col space-y-4 p-6 bg-background/30 rounded-lg border border-primary/20 shadow-sm max-w-4xl w-full">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-medium text-primary/80">(serverless applications deployed)</h2>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary border-2 border-primary/30 hover:bg-primary/20 hover:border-primary/50 rounded transition-all font-mono"
        >
          <Plus className="h-4 w-4" />
          Generate build for deployment
        </button>
      </div>

      {isLoading ? (
        <p className="text-primary/30 text-sm italic text-center py-8">Loading applications...</p>
      ) : apps.length === 0 ? (
        <p className="text-primary/30 text-sm italic text-center py-8">No applications deployed yet</p>
      ) : (
        <div className="space-y-3">
          {apps.map((app) => (
            <div
              key={app.app_name}
              className="flex justify-between items-center p-4 rounded bg-background/50 border border-primary/10 hover:border-primary/20 transition-colors group"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-base font-medium text-primary/90">{app.app_name}</h3>
                  <span className="text-xs text-primary/50 bg-primary/5 px-2 py-1 rounded">{app.framework}</span>
                  <span className="text-xs text-primary/50">Port: {app.port}</span>
                </div>
                <a
                  href={app.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary/60 hover:text-primary/80 flex items-center gap-1 mt-1"
                >
                  {app.url}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      <BuildModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSuccess={handleBuildSuccess} />
    </div>
  )
}
