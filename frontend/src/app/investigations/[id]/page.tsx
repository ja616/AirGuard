"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { 
  fetchInvestigation, 
  fetchTimeline, 
  fetchReport,
  fetchEvidence,
  fetchGraph
} from "@/lib/api";
import { 
  ResizableHandle, 
  ResizablePanel, 
  ResizablePanelGroup 
} from "@/components/ui/resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { 
  Activity, CheckCircle2, AlertTriangle, Play, Pause, Download, Send, ListTree 
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { useInvestigationSocket } from "@/hooks/useInvestigationSocket";
import { CorrelationGraph } from "@/components/investigations/CorrelationGraph";
import { EvidenceViewer } from "@/components/investigations/EvidenceViewer";

export default function InvestigationWorkspace() {
  const params = useParams();
  const id = params.id as string;

  const { data: inv, isLoading, isError } = useQuery({
    queryKey: ["investigations", id],
    queryFn: () => fetchInvestigation(id),
    refetchInterval: 2000,
    retry: false,
  });

  const isCompleted = inv?.state === "Completed";
  const isFailed = inv?.state === "Failed";

  const { isConnected } = useInvestigationSocket(id, !isCompleted && !isFailed);

  const { data: timeline } = useQuery({
    queryKey: ["timeline", id],
    queryFn: () => fetchTimeline(id),
    refetchInterval: 5000,
    retry: false,
  });

  const { data: report } = useQuery({
    queryKey: ["report", id],
    queryFn: () => fetchReport(id),
    refetchInterval: 5000,
    retry: false,
  });

  const { data: evidence } = useQuery({
    queryKey: ["evidence", id],
    queryFn: () => fetchEvidence(id),
    refetchInterval: 5000,
    retry: false,
  });

  const { data: graph } = useQuery({
    queryKey: ["graph", id],
    queryFn: () => fetchGraph(id),
    refetchInterval: 5000,
    retry: false,
  });

  if (isLoading || !inv) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-zinc-500 animate-pulse">Loading workspace...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-full items-center justify-center flex-col gap-3">
        <div className="text-rose-400 font-medium">Investigation not found</div>
        <div className="text-zinc-500 text-sm">ID: {id}</div>
        <a href="/investigations" className="text-indigo-400 text-sm underline">Back to Investigations</a>
      </div>
    );
  }

  const isWaiting = inv?.state === "ReadyForReview";

  const r = report?.content;
  const isPendingSlack = inv?.state === "SlackDispatch";

  const getSlackStatus = () => {
    if (isCompleted || isWaiting) return { status: "Investigation summary dispatched to Slack.", color: "text-emerald-400" };
    if (isFailed) return { status: "Failed", color: "text-rose-400" };
    if (isPendingSlack) return { status: "Pending", color: "text-amber-400" };
    return { status: "Awaiting Report", color: "text-zinc-500" };
  };

  const slackInfo = getSlackStatus();

  return (
    <div className="h-full flex flex-col bg-zinc-950 overflow-y-auto">
      {/* 1. INCIDENT SUMMARY */}
      <div className="p-6 border-b border-zinc-800 bg-zinc-900/40">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-zinc-100">
              Investigation: {id.split('-')[0]}
            </h1>
            <div className="flex items-center space-x-4 mt-2">
              <Badge variant="outline" className={
                isCompleted ? "text-emerald-400 border-emerald-900" : 
                isFailed ? "text-rose-400 border-rose-900" :
                "text-indigo-400 border-indigo-900"
              }>
                {inv.state}
              </Badge>
              {!isConnected && !isCompleted && !isFailed && (
                <Badge variant="outline" className="text-amber-400 border-amber-900 animate-pulse">
                  Reconnecting...
                </Badge>
              )}
              <span className="text-xs font-mono text-zinc-500">ENV: {inv.metadata.airflow_environment}</span>
              <span className="text-xs font-mono text-zinc-500">Duration: {inv.metadata.duration_seconds ? `${inv.metadata.duration_seconds}s` : "Ongoing"}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">External System</div>
            <div className={`text-sm font-medium flex items-center justify-end ${slackInfo.color}`}>
              <Send className="w-3 h-3 mr-1.5" />
              {slackInfo.status}
            </div>
          </div>
        </div>

        {/* Detailed Summary Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <div className="p-4 bg-zinc-900 rounded-md border border-zinc-800">
            <h3 className="text-xs text-zinc-500 uppercase font-semibold mb-1">Classification</h3>
            <div className="text-sm text-zinc-200 font-medium">
              {r?.incident_classification || (isFailed ? <span className="text-rose-500">Failed</span> : "Analyzing...")}
            </div>
          </div>
          <div className="p-4 bg-zinc-900 rounded-md border border-zinc-800">
            <h3 className="text-xs text-zinc-500 uppercase font-semibold mb-1">Confidence</h3>
            <div className="text-sm text-zinc-200 font-medium">
              {r?.confidence ? `${r.confidence.level} (${Math.round(r.confidence.score * 100)}%)` : (isFailed ? <span className="text-rose-500">Failed</span> : "Scoring...")}
            </div>
          </div>
          <div className="p-4 bg-zinc-900 rounded-md border border-zinc-800">
            <h3 className="text-xs text-zinc-500 uppercase font-semibold mb-1">Root Cause</h3>
            <div className="text-sm text-zinc-200 font-medium line-clamp-2">
              {r?.root_cause || (isFailed ? <span className="text-rose-500">Failed</span> : "Investigating...")}
            </div>
          </div>
          <div className="p-4 bg-zinc-900 rounded-md border border-zinc-800">
            <h3 className="text-xs text-zinc-500 uppercase font-semibold mb-1">Blast Radius</h3>
            <div className="text-sm text-zinc-200 font-medium">
              {r?.blast_radius ? (
                r.blast_radius.summary?.length > 0 ? (
                  <div className="space-y-1 text-zinc-300 mt-1 font-normal text-xs">
                    {r.blast_radius.summary.map((item: string, i: number) => (
                      <div key={i}>{item}</div>
                    ))}
                  </div>
                ) : (
                  `${r.blast_radius.affected_workflows?.length || 0} Workflows, ${r.blast_radius.affected_aws_resources?.length || 0} Resources`
                )
              ) : (isFailed ? <span className="text-rose-500">Failed</span> : "Assessing...")}
            </div>
          </div>
        </div>
        
        {/* Progress Bar (if running) */}
        {!isCompleted && !isFailed && (
          <div className="mt-6 flex items-center space-x-4">
            <span className="text-xs font-medium text-zinc-400 w-16">Progress</span>
            <Progress value={inv.progress} className="h-2 bg-zinc-800 flex-1" />
            <span className="text-xs font-mono text-zinc-400">{Math.round(inv.progress)}%</span>
          </div>
        )}
      </div>

      {/* Main Content Tabs */}
      <div className="flex-1 p-6">
        <Tabs defaultValue="report" className="h-full flex flex-col">
          <TabsList className="bg-zinc-900 border border-zinc-800 mb-6 inline-flex w-fit">
            <TabsTrigger value="report">Operational Report</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="evidence">Evidence</TabsTrigger>
            <TabsTrigger value="graph">Correlation Graph</TabsTrigger>
            <TabsTrigger value="raw">Raw Data</TabsTrigger>
          </TabsList>

          <TabsContent value="report" className="flex-1 mt-0">
            {r ? (
              <div className="space-y-8 max-w-4xl">
                <section>
                  <h2 className="text-lg font-semibold text-zinc-100 mb-2">Executive Summary</h2>
                  <div className="text-sm text-zinc-300 leading-relaxed prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{r.executive_summary}</ReactMarkdown>
                  </div>
                </section>
                <Separator className="bg-zinc-800" />
                <section>
                  <h2 className="text-lg font-semibold text-zinc-100 mb-2">Root Cause & Confidence</h2>
                  <div className="text-sm text-zinc-300 leading-relaxed mb-4 prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{r.root_cause}</ReactMarkdown>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-emerald-950/30 border border-emerald-900/50 p-4 rounded-md">
                      <h4 className="text-xs font-semibold text-emerald-400 mb-2 uppercase">Supporting Factors</h4>
                      <ul className="text-sm text-zinc-400 space-y-1 list-disc pl-4">
                        {r.confidence?.reasons?.map((reason: string, i: number) => <li key={i}>{reason}</li>) || <li>None</li>}
                      </ul>
                    </div>
                    <div className="bg-rose-950/30 border border-rose-900/50 p-4 rounded-md">
                      <h4 className="text-xs font-semibold text-rose-400 mb-2 uppercase">Contradictory Factors</h4>
                      <ul className="text-sm text-zinc-400 space-y-1 list-disc pl-4">
                        {r.confidence?.penalties?.map((penalty: string, i: number) => <li key={i}>{penalty}</li>) || <li>None</li>}
                      </ul>
                    </div>
                  </div>
                </section>
                <Separator className="bg-zinc-800" />
                <section>
                  <h2 className="text-lg font-semibold text-zinc-100 mb-2">Correlation Findings</h2>
                  <div className="space-y-3">
                    {r.correlation_summary?.map((c: any, i: number) => (
                      <div key={i} className="flex items-start space-x-3 p-3 bg-zinc-900 border border-zinc-800 rounded-md">
                        <AlertTriangle className={`h-4 w-4 mt-0.5 ${c.severity === 'high' ? 'text-rose-400' : 'text-amber-400'}`} />
                        <div>
                          <div className="text-sm text-zinc-200">{c.finding}</div>
                          <div className="text-xs text-zinc-500 mt-1">Source: {c.source}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
                <Separator className="bg-zinc-800" />
                <section>
                  <h2 className="text-lg font-semibold text-zinc-100 mb-2">Suggested Next Steps</h2>
                  <div className="space-y-3">
                    {r.suggested_next_steps?.map((rec: string, i: number) => (
                      <div key={i} className="p-3 bg-indigo-950/20 border border-indigo-900/50 text-sm text-zinc-300 rounded-md">
                        {rec}
                      </div>
                    ))}
                  </div>
                </section>
                
                {(isWaiting || isCompleted) && (
                  <div className="pt-6 pb-2">
                    <Button className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium">
                      Review Findings
                    </Button>
                  </div>
                )}
              </div>
            ) : isFailed ? (
              <div className="flex flex-col items-center justify-center h-64 text-rose-500">
                <AlertTriangle className="w-8 h-8 mb-4 opacity-80" />
                <div className="font-medium">Pipeline Execution Failed</div>
                <div className="text-sm text-zinc-500 mt-2">The investigation encountered a critical error (likely missing AWS telemetry credentials) and aborted before the report could be generated.</div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-zinc-500 animate-pulse">Report generation pending...</div>
            )}
          </TabsContent>

          <TabsContent value="timeline" className="flex-1 mt-0">
             <div className="max-w-3xl space-y-6">
                {timeline ? (
                  timeline.events.map((evt: any, idx: number) => (
                    <div key={idx} className="relative pl-6 border-l-2 border-zinc-800 pb-2">
                      <div className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-indigo-500" />
                      <div className="text-xs font-mono text-zinc-500">{new Date(evt.timestamp).toLocaleTimeString()}</div>
                      <div className="text-sm text-zinc-300 mt-1">{evt.event}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-zinc-500 italic">Timeline not available yet.</div>
                )}
              </div>
          </TabsContent>

          <TabsContent value="evidence" className="flex-1 mt-0 h-[600px]">
            <EvidenceViewer evidence={evidence} />
          </TabsContent>

          <TabsContent value="graph" className="flex-1 mt-0 h-[600px] border border-zinc-800 rounded-md overflow-hidden">
            <CorrelationGraph graphData={graph} />
          </TabsContent>

          <TabsContent value="raw" className="flex-1 mt-0">
             <div className="bg-zinc-950 p-4 border border-zinc-800 rounded-md max-w-5xl">
                <h3 className="text-zinc-100 text-sm font-medium mb-4">Raw Data Inspector</h3>
                <pre className="text-xs text-zinc-400 font-mono overflow-auto max-h-[600px]">
                  {JSON.stringify(r || inv, null, 2)}
                </pre>
             </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
