
"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  accessToken: string;
  sessionId: string;
  apiBase?: string; // default 127.0.0.1:8000
};

export default function LiveTranscriber({
  accessToken,
  sessionId,
  apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000",
}: Props) {
  const [status, setStatus] = useState<"idle" | "recording" | "stopped">("idle");
  const [bytesSent, setBytesSent] = useState(0);

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
    setStatus("idle");
    setBytesSent(0);

    // 1) get mic
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    // 2) open WS
    const url = new URL("/api/v1/ws/transcribe", apiBase);
    url.searchParams.set("session_id", sessionId);
    url.searchParams.set("token", accessToken);

    const ws = new WebSocket(url.toString().replace("http", "ws"));
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      // 3) start recorder AFTER ws is open
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (!e.data || e.data.size === 0) return;
        const buf = await e.data.arrayBuffer();
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(buf); // send as binary
          setBytesSent((v) => v + buf.byteLength);
        }
      };

      recorder.onerror = (ev) => console.error("MediaRecorder error:", ev);

      // timeslice so we actually get periodic chunks
      recorder.start(1000); // 1s
      setStatus("recording");
    };

    ws.onmessage = (ev) => {
      // optional debug (if server sends acks/status)
      // console.log("WS message:", ev.data);
    };

    ws.onclose = () => setStatus("stopped");
    ws.onerror = (e) => console.error("WS error:", e);
  }

  async function stop() {
    // stop recorder -> triggers final dataavailable with last chunk
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
      await done; // wait for the last chunk to be emitted & sent
    }

    // tell server we’re done (after last chunk sent)
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send("end");
      ws.close();
    }

    // stop tracks
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setStatus("stopped");
  }

  return (
    <div className="space-y-2">
      <div className="text-sm text-gray-600">
        Status: <b>{status}</b> • Bytes sent: <b>{bytesSent}</b>
      </div>
      <div className="space-x-2">
        <button
          className="rounded-md border px-3 py-2 hover:bg-gray-50"
          onClick={start}
          disabled={status === "recording"}
        >
          Start live
        </button>
        <button
          className="rounded-md border px-3 py-2 hover:bg-gray-50"
          onClick={stop}
          disabled={status !== "recording"}
        >
          Stop
        </button>
      </div>
    </div>
  );
}
