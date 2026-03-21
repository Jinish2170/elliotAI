"use client";

import { useAuditStore } from "@/lib/store";
import { useCallback, useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const _wsBase = process.env.NEXT_PUBLIC_WS_URL || "localhost:8000";
const WS_BASE = _wsBase.startsWith("ws") ? _wsBase : `ws://${_wsBase}`;

// Debug logging
const debugLog = (msg: string, data?: any) => {
	console.log(`[useAuditStream] ${msg}`, data);
};

export function useAuditStream(auditId: string | null, url?: string, tier?: string) {
	const wsRef = useRef<WebSocket | null>(null);
	const store = useAuditStore();

	const connect = useCallback(() => {
		if (!auditId) {
			debugLog("No auditId, returning");
			return;
		}

		debugLog("Connecting to WS", { auditId, url, tier, WS_BASE });

		// Set audit info (URL + tier) on the store before connecting
		if (url) {
			store.setAudit(auditId, url, tier || "standard_audit");
			debugLog("setAudit called", { auditId, url, tier });
		} else {
			store.setStatus("connecting");
			debugLog("setStatus(connecting) called");
		}

		const wsUrl = `${WS_BASE}/api/audit/stream/${auditId}`;
		debugLog("Creating WebSocket", { wsUrl });

		const ws = new WebSocket(wsUrl);
		wsRef.current = ws;

		ws.onopen = () => {
			debugLog("WebSocket OPEN");
			store.setStatus("running");
		};

		ws.onmessage = (event) => {
			debugLog("WS message received", { data: event.data.substring?.(0, 100) });
			try {
				const data = JSON.parse(event.data);
				store.handleEvent(data);
			} catch (e) {
				console.error("[useAuditStream] JSON parse error:", e);
			}
		};

		ws.onerror = (err) => {
			console.error("[useAuditStream] WebSocket error:", err);
			// Update store with error - use getState to avoid recursion
			const store2 = useAuditStore.getState();
			if (store2.status !== "error") {
				useAuditStore.setState({ status: "error", error: "WebSocket connection failed" });
			}
		};

		ws.onclose = async (event) => {
			debugLog("WebSocket closed", { code: event.code, reason: event.reason });
			// Check final status
			const store2 = useAuditStore.getState();
			const currentStatus = store2.status;
			if (currentStatus === "running") {
				if (event.code !== 1000) {
					store.setStatus("error");
				} else {
					try {
						const res = await fetch(`${API_URL}/api/audit/${auditId}/status`);
						if (res.ok) {
							const data = await res.json();
							if (data.status === "completed") {
								store.setStatus("complete");
							} else if (data.status === "error") {
								store.setStatus("error");
							}
						}
					} catch {
						// Ignore
					}
				}
			}
		};

		return ws;
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [auditId]);

	debugLog("useAuditStream render", { auditId, status: store.status });

	useEffect(() => {
		debugLog("useEffect running", { auditId });
		const ws = connect();
		return () => {
			debugLog("Cleanup - closing WS");
			if (ws && ws.readyState <= WebSocket.OPEN) {
				ws.close();
			}
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
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