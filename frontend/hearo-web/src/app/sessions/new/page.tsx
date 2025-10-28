"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { createSession, uploadSessionAudio } from "@/lib/api";
import Recorder from "@/components/Recorder";

export default function NewSessionPage() {
  const { user, accessToken } = useAuth(); // <-- get token from context
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [role, setRole] = useState<"student" | "professional">("student");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleCreateAndUpload(blob?: Blob) {
    // must be logged in and have a token
    if (!user || !accessToken) {
      router.replace("/login");
      return;
    }

    try {
      setBusy(true);
      setMsg("Creating session…");

      // create the session
      const s = await createSession(accessToken, { title, role });

      // decide what to upload (recorded blob vs picked file)
      let uploadBlob: Blob | File | null = null;
      let filename = "audio.webm";

      if (blob) {
        uploadBlob = blob;
        filename = "audio.webm";
      } else if (file) {
        uploadBlob = file;
        filename = file.name || "audio.bin";
      }

      // upload if we have audio
      if (uploadBlob) {
        setMsg("Uploading audio…");
        await uploadSessionAudio(accessToken, s.id, uploadBlob, filename);
      }

      setMsg("Done! Redirecting…");
      router.push("/dashboard");
    } catch (e: any) {
      setMsg(e.message || "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="max-w-2xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">New Session</h1>

      <div className="space-y-3 border rounded-2xl p-4">
        <label className="block">
          <span className="text-sm">Title</span>
          <input
            className="mt-1 w-full rounded border px-3 py-2"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Class 1: Linear Algebra"
          />
        </label>

        <label className="block">
          <span className="text-sm">Role</span>
          <select
            className="mt-1 w-full rounded border px-3 py-2 bg-white"
            value={role}
            onChange={(e) => setRole(e.target.value as "student" | "professional")}
          >
            <option value="student">Student</option>
            <option value="professional">Working professional</option>
          </select>
        </label>

        <div className="space-y-2">
          <span className="text-sm">Upload audio file</span>
          <input
            type="file"
            accept=".wav,.mp3,.m4a,.webm,.mp4,.ogg"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <div>
          <span className="text-sm">Or record via mic</span>
          <div className="mt-2">
            <Recorder onBlobReady={(b) => handleCreateAndUpload(b)} />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            disabled={busy}
            onClick={() => handleCreateAndUpload()}
            className="rounded border px-4 py-2 disabled:opacity-60"
          >
            {busy ? "Working…" : "Create session"}
          </button>

          {file && (
            <button
              disabled={busy}
              onClick={() => handleCreateAndUpload()}
              className="rounded border px-4 py-2 disabled:opacity-60"
            >
              {busy ? "Uploading…" : "Create + Upload file"}
            </button>
          )}
        </div>

        {msg && <p className="text-sm text-gray-700">{msg}</p>}
      </div>
    </main>
  );
}
