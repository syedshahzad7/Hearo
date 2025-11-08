"use client";

import { useAuth } from "@/context/AuthContext";
import LiveTranscriber from "@/components/LiveTranscriber";
import { useParams } from "next/navigation";

export default function LivePage() {
  const { user } = useAuth();
  const { id } = useParams<{ id: string }>();   // <- works in client components
  const accessToken = (typeof window !== "undefined"
    ? localStorage.getItem("access_token")
    : "") || "";

  if (!id) {
    return (
      <main className="max-w-3xl mx-auto p-6">
        <p className="text-red-600">No session id in URL.</p>
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">Live transcription</h1>
      <LiveTranscriber accessToken={accessToken} sessionId={String(id)} />
    </main>
  );
}