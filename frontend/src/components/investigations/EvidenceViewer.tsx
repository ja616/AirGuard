"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, Cloud, Terminal, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface EvidenceViewerProps {
  evidence?: any;
}

export function EvidenceViewer({ evidence }: EvidenceViewerProps) {
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

  if (!evidence || !evidence.collected) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500">
        Collecting evidence...
      </div>
    );
  }

  // Group evidence by source
  const groupedEvidence = evidence.collected.reduce((acc: any, ev: any) => {
    if (!acc[ev.source]) acc[ev.source] = [];
    acc[ev.source].push(ev);
    return acc;
  }, {});

  const toggleExpand = (idx: string) => {
    setExpandedKeys(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <ScrollArea className="h-full p-6">
      <div className="space-y-8 max-w-4xl pb-10">
        <div className="mb-2">
          <h2 className="text-lg font-medium text-zinc-100">Collected Evidence</h2>
          <p className="text-sm text-zinc-400">Raw signals and logs aggregated during the investigation, grouped by source system.</p>
        </div>

        {Object.keys(groupedEvidence).map((source) => {
          const items = groupedEvidence[source];
          const isDatabase = source.toLowerCase().includes("postgres") || source.toLowerCase().includes("airflow");

          return (
            <div key={source} className="space-y-4">
              <div className="flex items-center space-x-2 border-b border-zinc-800 pb-2">
                {isDatabase ? (
                  <Database className="h-5 w-5 text-emerald-400" />
                ) : (
                  <Cloud className="h-5 w-5 text-amber-400" />
                )}
                <h3 className="text-md font-semibold text-zinc-200">{source}</h3>
                <Badge variant="outline" className="ml-2 text-xs bg-zinc-900 border-zinc-800 text-zinc-400">
                  {items.length} items
                </Badge>
              </div>

              <div className="space-y-3">
                {items.map((ev: any, idx: number) => {
                  const itemKey = `${source}-${idx}`;
                  const isExpanded = !!expandedKeys[itemKey];
                  const hasError = JSON.stringify(ev.raw_payload || {}).toLowerCase().includes("error") || 
                                   JSON.stringify(ev.raw_payload || {}).toLowerCase().includes("fail");
                  
                  return (
                    <Card key={idx} className="bg-zinc-900 border-zinc-800 overflow-hidden">
                      <div className="flex items-center justify-between p-3 bg-zinc-950/50">
                        <div className="flex items-center space-x-3">
                          {hasError ? (
                            <AlertTriangle className="h-4 w-4 text-rose-500" />
                          ) : (
                            <Terminal className="h-4 w-4 text-zinc-500" />
                          )}
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-zinc-200">
                              {hasError ? "Anomaly Detected" : "Telemetry Payload"}
                            </span>
                            <span className="text-xs text-zinc-500 flex items-center space-x-2">
                              <span>Timestamp: {new Date().toLocaleTimeString()}</span>
                              <span className="text-zinc-700">•</span>
                              <span className={hasError ? "text-rose-500/80" : "text-emerald-500/80"}>
                                Severity: {hasError ? "High" : "Low"}
                              </span>
                            </span>
                          </div>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-zinc-400 hover:text-zinc-100 h-8"
                          onClick={() => toggleExpand(itemKey)}
                        >
                          {isExpanded ? "Hide Details" : "Expand Details"}
                          {isExpanded ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
                        </Button>
                      </div>

                      {isExpanded && (
                        <CardContent className="p-0 border-t border-zinc-800">
                          <div className="bg-black/50 p-4">
                            <pre className="text-xs font-mono text-zinc-300 whitespace-pre-wrap">
                              <code>{JSON.stringify(ev.raw_data, null, 2)}</code>
                            </pre>
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
