"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchInvestigations } from "@/lib/api";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";

export default function InvestigationsPage() {
  const router = useRouter();
  
  const { data: investigations, isLoading } = useQuery({
    queryKey: ["investigations"],
    queryFn: fetchInvestigations,
    refetchInterval: 2000,
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-zinc-500 animate-pulse">Loading investigations...</div>
      </div>
    );
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case "COMPLETED": return "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20";
      case "FAILED": return "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20";
      case "WAITING_APPROVAL": return "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20";
      default: return "bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20";
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Investigations</h1>
        <p className="text-sm text-zinc-400">All recent investigation runs</p>
      </div>

      <div className="rounded-md border border-zinc-800 bg-zinc-900 overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-950/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400 w-[100px]">ID</TableHead>
              <TableHead className="text-zinc-400">Environment</TableHead>
              <TableHead className="text-zinc-400">State</TableHead>
              <TableHead className="text-zinc-400">Started By</TableHead>
              <TableHead className="text-zinc-400 text-right">Started</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {investigations?.map((inv) => (
              <TableRow 
                key={inv.id}
                className="border-zinc-800 cursor-pointer hover:bg-zinc-800/50 transition-colors"
                onClick={() => router.push(`/investigations/${inv.id}`)}
              >
                <TableCell className="font-mono text-zinc-300">
                  {inv.id.substring(0, 8)}
                </TableCell>
                <TableCell className="font-medium text-zinc-200">
                  {inv.metadata.airflow_environment}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className={`${getStateColor(inv.state)} border-0`}>
                    {inv.state}
                  </Badge>
                </TableCell>
                <TableCell className="text-zinc-400">
                  {inv.metadata.started_by}
                </TableCell>
                <TableCell className="text-right text-zinc-400 text-sm">
                  {formatDistanceToNow(new Date(inv.metadata.started_at), { addSuffix: true })}
                </TableCell>
              </TableRow>
            ))}
            {(!investigations || investigations.length === 0) && (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-zinc-500">
                  No investigations found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
