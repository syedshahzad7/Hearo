"use client";
import React, { useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

type LiveMsg =
  | { type: "partial"; seq: number; text: string }
  | { type: "pong" }
  | { type: "error"; error: string; detail?: string }
  | { type: "closed" };

export default function LiveTranscriber({
  accessToken,
  sessionId,
}: {
  accessToken: string;
  sessionId: string;
}) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [liveText, setLiveText] = useState<Array<{ seq: number; text: string }>>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, [ws]);

  async function start() {
    const url = `${API_BASE.replace("http", "ws")}/api/v1/ws/transcribe?session_id=${encodeURIComponent(
      sessionId
    )}&token=${encodeURIComponent(accessToken)}`;

    const socket = new WebSocket(url);
    setWs(socket);

    socket.onmessage = (ev) => {
      try {
        const msg: LiveMsg = JSON.parse(ev.data);
        if (msg.type === "partial") {
          setLiveText((prev) => [...prev, { seq: msg.seq, text: msg.text }]);
        }
      } catch {}
    };

    socket.onopen = async () => {
      // mic
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

      mr.ondataavailable = async (e) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;
        const blob = e.data;
        const b64 = await blobToBase64(blob);
        socket.send(
          JSON.stringify({
            type: "audio",
            seq: Date.now(),
            mime: blob.type || "audio/webm;codecs=opus",
            b64,
          })
        );
      };
      // send every 1000ms
      mr.start(1000);
      mediaRecorderRef.current = mr;
      setIsRecording(true);
    };
  }

  function stop() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "close" }));
    }
    setIsRecording(false);
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button
          onClick={start}
          disabled={isRecording}
          className="px-3 py-2 rounded border"
        >
          {isRecording ? "Recording…" : "Start live transcription"}
        </button>
        <button
          onClick={stop}
          disabled={!isRecording}
          className="px-3 py-2 rounded border"
        >
          Stop
        </button>
      </div>

      <div className="border rounded-lg p-3 h-64 overflow-auto bg-white">
        {liveText.length === 0 ? (
          <p className="text-sm text-gray-500">Live transcript will appear here…</p>
        ) : (
          <ul className="space-y-1">
            {liveText.map((c) => (
              <li key={c.seq} className="text-sm">
                {c.text}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const r = new FileReader();
    r.onload = () => {
      const res = (r.result as string) || "";
      resolve(res.split(",")[1] || ""); // remove data:...;base64,
    };
    r.readAsDataURL(blob);
  });
}
