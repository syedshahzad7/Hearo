
"use client";

import { useAuth } from "@/context/AuthContext";
import LiveTranscriber from "@/components/LiveTranscriber";

export default function LivePage({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const accessToken = localStorage.getItem("access_token") || "";

  return (
    <main className="max-w-3xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">Live transcription</h1>
      <LiveTranscriber accessToken={accessToken} sessionId={params.id} />
    </main>
  );
}
