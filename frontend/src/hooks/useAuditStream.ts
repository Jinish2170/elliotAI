"use client";

import { useAuditStore } from "@/lib/store";
import { useCallback, useEffect, useRef } from "react";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useAuditStream(auditId: string | null, url?: string, tier?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const store = useAuditStore();

  const connect = useCallback(() => {
    if (!auditId) return;

    // Set audit info (URL + tier) on the store before connecting
    if (url) {
      store.setAudit(auditId, url, tier || "standard_audit");
    } else {
      store.setStatus("connecting");
    }

    const ws = new WebSocket(`${WS_BASE}/api/audit/stream/${auditId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      store.setStatus("running");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        store.handleEvent(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      store.setStatus("error");
    };

    ws.onclose = (event) => {
      // Normal close or audit ended
      if (store.status !== "complete" && store.status !== "error") {
        if (event.code !== 1000) {
          store.setStatus("error");
        }
      }
    };

    return ws;
  }, [auditId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const ws = connect();
    return () => {
      if (ws && ws.readyState <= WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
      wsRef.current.close();
    }
  }, []);

  return {
    disconnect,
    ...store,
  };
}
