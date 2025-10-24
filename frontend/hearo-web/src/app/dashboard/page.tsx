"use client";

import Protected from "@/components/Protected";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <Protected>
      <main className="p-8 space-y-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-700">Welcome, {user?.full_name}!</p>
        <button
          onClick={logout}
          className="rounded-md border px-4 py-2 hover:bg-gray-50"
        >
          Log out
        </button>
      </main>
    </Protected>
  );
}
