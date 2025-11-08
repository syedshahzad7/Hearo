"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Protected from "@/components/Protected";
import { useAuth } from "@/context/AuthContext";
import { listSessions, createSession, type Session } from "@/lib/api";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [title, setTitle] = useState("");
  const [role, setRole] = useState<"student" | "professional">("student");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // fetch sessions on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    listSessions(token)
      .then(setSessions)
      .catch(() => setError("Failed to load sessions"));
  }, []);

  const handleCreate = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Not logged in.");
      return;
    }

    try {
      setCreating(true);
      const created = await createSession(token, {
        title: title.trim() || undefined,
        role,
      });
      setSessions((prev) => [created, ...prev]);
      router.push(`/sessions/${created.id}/live`);
    } catch (e: any) {
      setError(e?.message || "Failed to create session");
    } finally {
      setCreating(false);
    }
  };

  const goLive = (id: string) => router.push(`/sessions/${id}/live`);

  return (
    <Protected>
      <main className="max-w-4xl mx-auto p-8 space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-gray-700">
              Welcome, {user?.full_name || user?.email}!
            </p>
          </div>
          <button
            onClick={logout}
            className="rounded-md border px-4 py-2 hover:bg-gray-50"
          >
            Log out
          </button>
        </header>

        {/* Create session card */}
        <section className="border rounded-xl p-4 space-y-4">
          <h2 className="text-lg font-semibold">Create a new session</h2>
          <div className="grid sm:grid-cols-3 gap-3">
            <input
              className="border rounded-lg px-3 py-2 sm:col-span-2"
              type="text"
              placeholder="Optional title (e.g. Lecture 1)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <select
              className="border rounded-lg px-3 py-2"
              value={role}
              onChange={(e) =>
                setRole(e.target.value as "student" | "professional")
              }
            >
              <option value="student">Student</option>
              <option value="professional">Professional</option>
            </select>
          </div>
          <button
            onClick={handleCreate}
            disabled={creating}
            className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-60"
          >
            {creating ? "Creating…" : "Create & go live"}
          </button>
          {error && <p className="text-red-600 text-sm">{error}</p>}
        </section>

        {/* Sessions list */}
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Your sessions</h2>
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-600">
              No sessions yet. Create one above to get started.
            </p>
          ) : (
            <ul className="divide-y rounded-xl border">
              {sessions.map((s) => (
                <li
                  key={s.id}
                  className="p-4 flex items-center justify-between gap-4"
                >
                  <div className="min-w-0">
                    <div className="font-medium truncate">
                      {s.title || "(untitled)"}{" "}
                      <span className="ml-2 text-xs px-2 py-0.5 border rounded-full">
                        {s.role}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      {s.status}{" "}
                      {s.created_at
                        ? `• ${new Date(s.created_at).toLocaleString()}`
                        : ""}
                    </div>
                  </div>
                  <button
                    onClick={() => goLive(s.id)}
                    className="px-3 py-1.5 rounded-lg border"
                    title="Open live transcription"
                  >
                    Go live
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </Protected>
  );
}
