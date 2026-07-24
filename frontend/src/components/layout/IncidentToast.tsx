"use client";

import { useEffect, useState, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchInvestigations } from "@/lib/api";
import { AlertTriangle, X } from "lucide-react";
import { useRouter } from "next/navigation";

export function IncidentToast() {
  const router = useRouter();
  const knownIds = useRef<Set<string>>(new Set());
  const [newIncident, setNewIncident] = useState<any | null>(null);

  const { data: investigations } = useQuery({
    queryKey: ["investigations"],
    queryFn: fetchInvestigations,
    refetchInterval: 3000,
  });

  useEffect(() => {
    if (!investigations) return;

    // First load with data: just record existing IDs, don't toast
    if (knownIds.current.size === 0 && investigations.length > 0) {
      knownIds.current = new Set(investigations.map((i) => i.id));
      return;
    }

    // Check for new IDs
    const currentIds = new Set(investigations.map((i) => i.id));
    const newIds = investigations.filter((i) => !knownIds.current.has(i.id));

    if (newIds.length > 0) {
      // Show the most recent new incident
      setNewIncident(newIds[0]);
      knownIds.current = currentIds;

      // Auto-hide after 10 seconds
      setTimeout(() => {
        setNewIncident(null);
      }, 10000);
    }
  }, [investigations]);

  if (!newIncident) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
      <div 
        className="bg-zinc-900 border-l-4 border-l-rose-500 border-y border-r border-zinc-800 rounded-r-md shadow-2xl p-4 pr-10 relative cursor-pointer hover:bg-zinc-800/80 transition-colors w-80"
        onClick={() => {
          setNewIncident(null);
          router.push(`/investigations/${newIncident.id}`);
        }}
      >
        <button 
          className="absolute top-2 right-2 text-zinc-500 hover:text-zinc-300"
          onClick={(e) => {
            e.stopPropagation();
            setNewIncident(null);
          }}
        >
          <X size={16} />
        </button>
        
        <div className="flex items-start gap-3">
          <div className="mt-0.5 bg-rose-500/20 p-1.5 rounded-full">
            <AlertTriangle className="text-rose-500" size={16} />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">🚨 New Incident Detected</h4>
            <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
              Investigation started for {newIncident.metadata?.airflow_environment || "production"} environment.
            </p>
            <div className="mt-2 text-xs font-medium text-indigo-400 hover:text-indigo-300">
              View investigation →
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
