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

		// Dynamically determine the WS base URL based on window.location
		// This prevents "localhost" being used when accessed remotely
		let dynamicWsBase = WS_BASE;
		if (typeof window !== "undefined") {
			const fallbackProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
			const apiHost = process.env.NEXT_PUBLIC_API_URL ? new URL(process.env.NEXT_PUBLIC_API_URL).host : "localhost:8000";
			
			// If NEXT_PUBLIC_WS_URL is provided explicitly, respect it.
			// Otherwise derive from API_URL or window.location
			if (!process.env.NEXT_PUBLIC_WS_URL) {
				dynamicWsBase = `${fallbackProtocol}//${apiHost}`;
				
				// Handle case where API is on same host but different port during dev
				if (apiHost.includes("localhost") || apiHost.includes("127.0.0.1")) {
					dynamicWsBase = `${fallbackProtocol}//${window.location.hostname}:8000`;
				}
			}
		}

		debugLog("Connecting to WS", { auditId, url, tier, dynamicWsBase });

		// Set audit info (URL + tier) on the store before connecting
		if (url) {
			store.setAudit(auditId, url, tier || "standard_audit");
			debugLog("setAudit called", { auditId, url, tier });
		} else {
			store.setStatus("connecting");
			debugLog("setStatus(connecting) called");
		}

		const wsUrl = `${dynamicWsBase}/api/audit/stream/${auditId}`;
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

		let isIntentionalClose = false;

		ws.onerror = (err) => {
			const isIntentionalClose = (ws as any).__isIntentionalClose;
			console.error("[useAuditStream] WebSocket error:", err, "readyState:", ws.readyState);
			if (isIntentionalClose) {
				debugLog("Ignoring error due to intentional close.");
				return;
			}
			// Update store with error - use getState to avoid recursion
			const store2 = useAuditStore.getState();
			if (store2.status !== "error") {
				useAuditStore.setState({ status: "error", error: "WebSocket connection failed" });
			}
		};

		// Attach to our local ref
		(ws as any).__isIntentionalClose = false;

		ws.onclose = async (event) => {
			const isIntentionalClose = (ws as any).__isIntentionalClose;
			debugLog("WebSocket closed", { code: event.code, reason: event.reason, isIntentionalClose });
			
			if (isIntentionalClose) return;

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
				(ws as any).__isIntentionalClose = true;
				ws.close();
			}
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [connect]);

	const disconnect = useCallback(() => {
		if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
			(wsRef.current as any).__isIntentionalClose = true;
			wsRef.current.close();
		}
	}, []);

	return {
		disconnect,
		...store,
	};
}