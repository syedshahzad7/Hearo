"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchMe, UserPublic } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchMe(token)
      .then(setUser)
      .catch(() => {
        // invalid/expired token
        localStorage.removeItem("access_token");
        setErr("Session expired. Please log in again.");
        router.replace("/login");
      });
  }, [router]);

  function logout() {
    localStorage.removeItem("access_token");
    router.push("/login");
  }

  return (
    <main className="min-h-screen p-8">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold">Hearo Dashboard</h1>
        <button onClick={logout} className="rounded-md px-3 py-2 border">
          Log out
        </button>
      </div>

      <section className="max-w-3xl mx-auto mt-6">
        {err && <p className="text-red-600">{err}</p>}
        {!user ? (
          <p>Loading your profile…</p>
        ) : (
          <div className="space-y-2 rounded-xl border p-4">
            <p><span className="font-semibold">Email:</span> {user.email}</p>
            <p><span className="font-semibold">Name:</span> {user.full_name || "—"}</p>
            <p><span className="font-semibold">Role:</span> {user.role}</p>
          </div>
        )}
      </section>
    </main>
  );
}