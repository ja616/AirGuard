import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface StateChangeEvent {
  id: string;
  new_state: string;
  progress: number;
}

export function useInvestigationSocket(investigationId: string, shouldConnect: boolean = true) {
  const queryClient = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!investigationId || !shouldConnect) {
      if (socketRef.current) socketRef.current.close();
      return;
    }

    let reconnectTimeout: NodeJS.Timeout;
    
    const connect = () => {
      const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/investigations/${investigationId}/stream`);
      
      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: StateChangeEvent = JSON.parse(event.data);
          
          // Optimistically update the investigation cache
          queryClient.setQueryData(["investigations", investigationId], (old: any) => {
            if (!old) return old;
            return {
              ...old,
              state: data.new_state,
              progress: data.progress,
            };
          });

          // Invalidate timeline, graph, and report since state changed
          queryClient.invalidateQueries({ queryKey: ["timeline", investigationId] });
          queryClient.invalidateQueries({ queryKey: ["graph", investigationId] });
          queryClient.invalidateQueries({ queryKey: ["report", investigationId] });
          
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Try to reconnect in 3s
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socketRef.current = ws;
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [investigationId, queryClient]);

  return { isConnected };
}
