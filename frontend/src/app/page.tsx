"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchMetrics, fetchHealth } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, CheckCircle2, Clock, XCircle, ListVideo, HeartPulse } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function Dashboard() {
  const { data: metrics, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: fetchMetrics,
    refetchInterval: 5000,
  });

  const { data: health, isLoading: isLoadingHealth } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  if (isLoadingMetrics || isLoadingHealth) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-zinc-500 animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  if (!metrics || !health) return null;

  const successRate = metrics.total_investigations > 0
    ? ((metrics.completed_investigations / metrics.total_investigations) * 100).toFixed(1)
    : "0.0";
    
  const chartData = [
    { name: "Completed", value: metrics.completed_investigations, color: "#34d399" },
    { name: "Failed", value: metrics.failed_investigations, color: "#f87171" },
  ];

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-zinc-400">AirGuard Operational Investigation Console</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Total Runs</CardTitle>
            <ListVideo className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_investigations}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Completed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">{metrics.completed_investigations}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-rose-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-rose-500">{metrics.failed_investigations}</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Success Rate</CardTitle>
            <Activity className="h-4 w-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-100">{successRate}%</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-100">{metrics.average_duration_seconds}s</div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">System Health</CardTitle>
            <HeartPulse className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${health.status === 'Healthy' ? 'text-emerald-400' : 'text-amber-400'}`}>
              {health.status}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-zinc-900 border-zinc-800 col-span-1">
          <CardHeader>
            <CardTitle className="text-zinc-100 text-lg">Investigation Outcomes</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: '#27272a'}} 
                  contentStyle={{backgroundColor: '#09090b', border: '1px solid #27272a', borderRadius: '6px'}} 
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-zinc-800 col-span-1">
          <CardHeader>
            <CardTitle className="text-zinc-100 text-lg">Subsystem Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex flex-col p-3 rounded bg-zinc-950/50 border border-zinc-800/50">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-300 font-medium">PostgreSQL Database</span>
                  <span className={`text-sm px-2 py-1 rounded-full ${health.database === 'Healthy' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-rose-400/10 text-rose-400'}`}>{health.database}</span>
                </div>
                {health.database !== 'Healthy' && (
                  <p className="text-xs text-rose-400/80 mt-2">Investigation persistence disabled. Engine cannot store artifacts.</p>
                )}
              </div>
              <div className="flex flex-col p-3 rounded bg-zinc-950/50 border border-zinc-800/50">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-300 font-medium">Apache Airflow</span>
                  <span className={`text-sm px-2 py-1 rounded-full ${health.airflow === 'Healthy' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-rose-400/10 text-rose-400'}`}>{health.airflow}</span>
                </div>
                {health.airflow !== 'Healthy' && (
                  <p className="text-xs text-rose-400/80 mt-2">DAG execution data unavailable. Task timelines cannot be reconstructed.</p>
                )}
              </div>
              <div className="flex flex-col p-3 rounded bg-zinc-950/50 border border-zinc-800/50">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-300 font-medium">AWS Interconnect</span>
                  <span className={`text-sm px-2 py-1 rounded-full ${health.aws === 'Healthy' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-rose-400/10 text-rose-400'}`}>{health.aws}</span>
                </div>
                {health.aws !== 'Healthy' && (
                  <p className="text-xs text-rose-400/80 mt-2">CloudWatch evidence unavailable. Infrastructure evidence will be incomplete.</p>
                )}
              </div>
              <div className="flex flex-col p-3 rounded bg-zinc-950/50 border border-zinc-800/50">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-300 font-medium">Slack Dispatcher</span>
                  <span className={`text-sm px-2 py-1 rounded-full ${health.slack === 'Healthy' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-rose-400/10 text-rose-400'}`}>{health.slack}</span>
                </div>
                {health.slack !== 'Healthy' && (
                  <p className="text-xs text-rose-400/80 mt-2">Operational dispatch disabled. Report notifications will not be sent.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
