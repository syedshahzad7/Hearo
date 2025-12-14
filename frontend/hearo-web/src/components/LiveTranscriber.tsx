// frontend/hearo-web/src/components/LiveTranscriber.tsx
"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  accessToken: string;
  sessionId: string;
  apiBase?: string; // default http://127.0.0.1:8000
};

type WSMsg =
  | { type: "ready"; session_id?: string }
  | { type: "partial"; seq: number; text: string }
  | { type: "pong" }
  | { type: "done" }
  | { type: "error"; message?: string; detail?: string };

export default function LiveTranscriber({
  accessToken,
  sessionId,
  apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000",
}: Props) {
  const [status, setStatus] = useState<
    "idle" | "connecting" | "recording" | "stopping" | "stopped" | "error"
  >("idle");
  const [bytesSent, setBytesSent] = useState(0);
  const [lastServerMsg, setLastServerMsg] = useState<string>("");
  const [partials, setPartials] = useState<Array<{ seq: number; text: string }>>(
    []
  );

  const wsRef = useRef<WebSocket | null>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    return () => {
      try {
        recRef.current?.stop();
      } catch {}
      try {
        wsRef.current?.close();
      } catch {}
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function start() {
    setStatus("connecting");
    setBytesSent(0);
    setLastServerMsg("");
    setPartials([]);

    // 1) mic permission
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    // 2) open WS
    const url = new URL("/api/v1/ws/transcribe", apiBase);
    url.searchParams.set("session_id", sessionId);
    url.searchParams.set("token", accessToken);

    const wsUrl = url.toString().replace(/^http/, "ws");
    const ws = new WebSocket(wsUrl);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (!e.data || e.data.size === 0) return;
        const buf = await e.data.arrayBuffer();

        const sock = wsRef.current;
        if (sock && sock.readyState === WebSocket.OPEN) {
          sock.send(buf); // send binary chunk
          setBytesSent((v) => v + buf.byteLength);
        }
      };

      recorder.onerror = (ev) => console.error("MediaRecorder error:", ev);

      recorder.start(1000); // 1s chunks
      setStatus("recording");
    };

    ws.onmessage = (ev) => {
      if (typeof ev.data !== "string") return;

      try {
        const msg = JSON.parse(ev.data) as WSMsg;

        if (msg.type === "ready") {
          setLastServerMsg("Server ready");
          return;
        }

        if (msg.type === "partial") {
          setPartials((prev) => [...prev, { seq: msg.seq, text: msg.text }]);
          return;
        }

        if (msg.type === "pong") {
          setLastServerMsg("pong");
          return;
        }

        if (msg.type === "done") {
          setLastServerMsg("done");
          // NOW it’s safe to close (server finished transcription + sends final)
          try {
            wsRef.current?.close();
          } catch {}
          setStatus("stopped");
          return;
        }

        if (msg.type === "error") {
          setLastServerMsg(
            `error: ${msg.message || ""} ${msg.detail ? `(${msg.detail})` : ""}`
          );
          setStatus("error");
        }
      } catch {
        // ignore malformed JSON
      }
    };

    ws.onclose = () => {
      // If we closed intentionally after "done", status is already set
      setStatus((s) => (s === "recording" || s === "connecting" ? "stopped" : s));
    };

    ws.onerror = (e) => {
      console.error("WS error:", e);
      setStatus("error");
    };
  }

  async function stop() {
    setStatus("stopping");

    // 1) stop recorder and wait for last chunk to flush
    const rec = recRef.current;
    if (rec && rec.state !== "inactive") {
      const done = new Promise<void>((resolve) => {
        const onStop = () => {
          rec.removeEventListener("stop", onStop);
          resolve();
        };
        rec.addEventListener("stop", onStop);
      });
      rec.stop();
      await done;
    }

    // 2) stop mic tracks (we are done capturing audio)
    streamRef.current?.getTracks().forEach((t) => t.stop());

    // 3) IMPORTANT: do NOT close WS here.
    // Send "end" and WAIT for server to respond with {type:"done"}
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send("end");
      setLastServerMsg("sent end; waiting for done…");
    } else {
      setStatus("stopped");
    }
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600">
        Status: <b>{status}</b> • Bytes sent: <b>{bytesSent}</b>
        {lastServerMsg ? (
          <>
            {" "}
            • Server: <b>{lastServerMsg}</b>
          </>
        ) : null}
      </div>

      <div className="space-x-2">
        <button
          className="rounded-md border px-3 py-2 hover:bg-gray-50"
          onClick={start}
          disabled={status === "recording" || status === "connecting" || status === "stopping"}
        >
          {status === "connecting" ? "Connecting..." : "Start live"}
        </button>
        <button
          className="rounded-md border px-3 py-2 hover:bg-gray-50"
          onClick={stop}
          disabled={status !== "recording"}
        >
          Stop
        </button>
      </div>

      <div className="border rounded-lg p-3 h-64 overflow-auto bg-white">
        {partials.length === 0 ? (
          <p className="text-sm text-gray-500">
            Live transcript will appear here…
          </p>
        ) : (
          <ul className="space-y-1">
            {partials.map((p) => (
              <li key={p.seq} className="text-sm">
                {p.text}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
