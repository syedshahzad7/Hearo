"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { registerUser } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<"student" | "professional">("student");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setOk(null);
    setLoading(true);
    try {
      await registerUser({ email, password, full_name: fullName, role });
      setOk("Account created! You can now log in.");
      setTimeout(() => router.push("/login"), 800);
    } catch (e: any) {
      setErr(e.message || "Failed to sign up.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-md space-y-4 border p-6 rounded-2xl">
        <h1 className="text-2xl font-bold">Create your Hearo account</h1>

        <label className="block">
          <span className="text-sm">Full name</span>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Syed Shahzad"
          />
        </label>

        <label className="block">
          <span className="text-sm">Email</span>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </label>

        <label className="block">
          <span className="text-sm">Role</span>
          <select
            className="mt-1 w-full rounded-md border px-3 py-2 bg-white"
            value={role}
            onChange={(e) => setRole(e.target.value as any)}
          >
            <option value="student">Student</option>
            <option value="professional">Working professional</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm">Password</span>
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Passw0rd!"
            required
          />
        </label>

        {err && <p className="text-red-600 text-sm">{err}</p>}
        {ok && <p className="text-green-600 text-sm">{ok}</p>}

        <button
          type="submit"
          className="w-full rounded-md px-4 py-2 bg-black text-white disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Creating..." : "Sign up"}
        </button>

        <p className="text-sm">
          Already have an account?{" "}
          <a href="/login" className="underline">
            Log in
          </a>
        </p>
      </form>
    </main>
  );
}