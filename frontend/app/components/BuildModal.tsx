"use client"

import type React from "react"
import { useState } from "react"
import { X } from "lucide-react"

interface BuildModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface EnvVar {
  key: string
  value: string
}

const backend_url = process.env.NEXT_PUBLIC_BACKEND_URL

export default function BuildModal({ isOpen, onClose, onSuccess }: BuildModalProps) {
  const [projectPath, setProjectPath] = useState("")
  const [appName, setAppName] = useState("")
  const [framework, setFramework] = useState("")
  const [port, setPort] = useState("")
  const [envVars, setEnvVars] = useState<EnvVar[]>([{ key: "", value: "" }])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")

  const handleAddEnvVar = () => {
    setEnvVars([...envVars, { key: "", value: "" }])
  }

  const handleRemoveEnvVar = (index: number) => {
    const newEnvVars = envVars.filter((_, i) => i !== index)
    setEnvVars(newEnvVars.length > 0 ? newEnvVars : [{ key: "", value: "" }])
  }

  const handleEnvVarChange = (index: number, field: "key" | "value", value: string) => {
    const newEnvVars = [...envVars]
    newEnvVars[index][field] = value
    setEnvVars(newEnvVars)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsSubmitting(true)

    try {
      // Convert env vars array to object
      const envVarsObject: Record<string, string> = {}
      envVars.forEach((env) => {
        if (env.key.trim()) {
          envVarsObject[env.key] = env.value
        }
      })

      const payload = {
        project_path: projectPath,
        app_name: appName,
        framework: framework,
        env_vars: envVarsObject,
        port: port ? Number.parseInt(port) : null,
      }

      console.log("[v0] Submitting build:", payload)

      const response = await fetch(`${backend_url}/build/lambda`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (data.success || data.succes) {
        // Reset form
        setProjectPath("")
        setAppName("")
        setFramework("")
        setPort("")
        setEnvVars([{ key: "", value: "" }])
        onSuccess()
      } else {
        setError(data.error || "Failed to build application")
      }
    } catch (err) {
      console.error("[v0] Error submitting build:", err)
      setError("Failed to submit build request")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0a0a0a] border-2 border-primary/30 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden shadow-2xl shadow-primary/20">
        <div className="bg-[#0a0a0a] border-b-2 border-primary/30 p-6 flex justify-between items-center">
          <h2 className="text-xl font-mono text-primary">(generate build for deployment)</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-primary/50 hover:text-primary hover:bg-primary/10 p-2 rounded transition-colors"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {error && (
              <div className="bg-red-500/10 border-2 border-red-500/30 text-red-400 p-3 rounded text-sm font-mono">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="projectPath" className="text-sm font-mono text-primary/90 block">
                Project Path
              </label>
              <input
                id="projectPath"
                type="text"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
                placeholder="/path/to/project"
                required
                className="w-full px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="appName" className="text-sm font-mono text-primary/90 block">
                App Name
              </label>
              <input
                id="appName"
                type="text"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                placeholder="my-app"
                required
                className="w-full px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="framework" className="text-sm font-mono text-primary/90 block">
                Framework
              </label>
              <select
                id="framework"
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                required
                className="w-full px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
              >
                <option value="">Select framework</option>
                <option value="nextjs">Next.js</option>
                <option value="vite">Vite</option>
              </select>
            </div>

            <div className="space-y-2">
              <label htmlFor="port" className="text-sm font-mono text-primary/90 block">
                Port (optional)
              </label>
              <input
                id="port"
                type="number"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="8000"
                className="w-full px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-sm font-mono text-primary/90">Environment Variables</label>
                <button
                  type="button"
                  onClick={handleAddEnvVar}
                  className="text-sm font-mono text-primary/70 hover:text-primary px-3 py-1 rounded hover:bg-primary/10 transition-colors border border-primary/20"
                >
                  + Add Variable
                </button>
              </div>
              <div className="space-y-2">
                {envVars.map((env, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={env.key}
                      onChange={(e) => handleEnvVarChange(index, "key", e.target.value)}
                      placeholder="KEY"
                      className="flex-1 px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
                    />
                    <input
                      type="text"
                      value={env.value}
                      onChange={(e) => handleEnvVarChange(index, "value", e.target.value)}
                      placeholder="value"
                      className="flex-1 px-4 py-3 border-2 border-primary/30 bg-[#0a0a0a] text-primary font-mono rounded focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all"
                    />
                    {envVars.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveEnvVar(index)}
                        className="text-primary/50 hover:text-primary p-2 rounded hover:bg-primary/10 transition-colors"
                        aria-label="Remove variable"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t-2 border-primary/20">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 font-mono text-primary/70 hover:text-primary hover:bg-primary/10 rounded border-2 border-primary/20 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-3 font-mono bg-primary/20 text-primary hover:bg-primary/30 rounded border-2 border-primary/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Building..." : "Build & Deploy"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
