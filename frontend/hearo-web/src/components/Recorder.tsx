"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  onBlobReady: (blob: Blob) => void;
};

export default function Recorder({ onBlobReady }: Props) {
  const [recording, setRecording] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunks = useRef<BlobPart[]>([]);

  useEffect(() => {
    return () => {
      // cleanup stream on unmount
      stream?.getTracks().forEach(t => t.stop());
    };
  }, [stream]);

  async function start() {
    const s = await navigator.mediaDevices.getUserMedia({ audio: true });
    setStream(s);
    const rec = new MediaRecorder(s, { mimeType: "audio/webm" });
    chunks.current = [];
    rec.ondataavailable = (e) => { if (e.data.size > 0) chunks.current.push(e.data); };
    rec.onstop = () => {
      const blob = new Blob(chunks.current, { type: "audio/webm" });
      onBlobReady(blob);
      s.getTracks().forEach(t => t.stop());
      setStream(null);
    };
    rec.start();
    recRef.current = rec;
    setRecording(true);
  }

  function stop() {
    recRef.current?.stop();
    setRecording(false);
  }

  return (
    <div className="border rounded-xl p-3">
      <p className="mb-2 text-sm">Mic recorder (WebM/Opus)</p>
      {!recording ? (
        <button onClick={start} className="rounded border px-3 py-1">Start</button>
      ) : (
        <button onClick={stop} className="rounded border px-3 py-1">Stop</button>
      )}
    </div>
  );
}
