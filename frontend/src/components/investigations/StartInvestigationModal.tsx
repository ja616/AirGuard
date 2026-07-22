"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Play, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE = "http://localhost:8000/api/v1";

export function StartInvestigationModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [dagId, setDagId] = useState("");
  const [failedNodeId, setFailedNodeId] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [executionState, setExecutionState] = useState("failed");
  const [investigationGoal, setInvestigationGoal] = useState("root_cause");
  const [environment, setEnvironment] = useState("prod");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dagId) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/investigations/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dag_id: dagId,
          failed_node_id: failedNodeId || undefined,
          severity,
          execution_state: executionState,
          investigation_goal: investigationGoal,
          environment,
        }),
      });

      const data = await res.json();
      if (res.ok && data.id) {
        setIsOpen(false);
        router.push(`/investigations/${data.id}`);
      } else {
        alert(`Failed to start investigation: ${JSON.stringify(data)}`);
      }
    } catch (err) {
      alert("Error connecting to AirGuard backend. Is it running?");
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    "w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-zinc-600";
  const selectCls = `${inputCls} cursor-pointer`;

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-900/20"
      >
        <Play size={16} className="mr-2" />
        Start Investigation
      </Button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl relative">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white"
            >
              <X size={20} />
            </button>
            <h2 className="text-xl font-semibold text-white mb-1">New Investigation</h2>
            <p className="text-sm text-zinc-400 mb-6">
              Trigger a deterministic root cause analysis from structured incident context.
            </p>

            <form onSubmit={handleStart} className="space-y-4">
              {/* Workflow ID */}
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1">
                  Workflow ID <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={dagId}
                  onChange={(e) => setDagId(e.target.value)}
                  placeholder="e.g. data_pipeline_etl"
                  className={inputCls}
                  required
                />
              </div>

              {/* Failed Node */}
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1">
                  Failed Node ID{" "}
                  <span className="text-zinc-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={failedNodeId}
                  onChange={(e) => setFailedNodeId(e.target.value)}
                  placeholder="e.g. extract_raw_data"
                  className={inputCls}
                />
              </div>

              {/* Severity + Goal */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1">
                    Severity
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className={selectCls}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1">
                    Investigation Goal
                  </label>
                  <select
                    value={investigationGoal}
                    onChange={(e) => setInvestigationGoal(e.target.value)}
                    className={selectCls}
                  >
                    <option value="root_cause">Root Cause</option>
                    <option value="impact_analysis">Impact Analysis</option>
                    <option value="cost_analysis">Cost Analysis</option>
                    <option value="performance">Performance</option>
                  </select>
                </div>
              </div>

              {/* Execution State + Environment */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1">
                    Execution State
                  </label>
                  <select
                    value={executionState}
                    onChange={(e) => setExecutionState(e.target.value)}
                    className={selectCls}
                  >
                    <option value="failed">Failed</option>
                    <option value="upstream_failed">Upstream Failed</option>
                    <option value="zombie">Zombie</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1">
                    Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value)}
                    className={selectCls}
                  >
                    <option value="prod">Production</option>
                    <option value="staging">Staging</option>
                    <option value="dev">Development</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsOpen(false)}
                  className="mr-2"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={loading || !dagId}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {loading ? (
                    <>
                      <Loader2 size={16} className="mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play size={16} className="mr-2" />
                      Start Analysis
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
