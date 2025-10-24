"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { UserPublic } from "@/lib/auth";
import { apiLogin, fetchMe } from "@/lib/api";
import { getAccessToken, saveTokens, clearTokens } from "@/lib/auth";
import { useRouter } from "next/navigation";

type AuthState = {
  user: UserPublic | null;
  loading: boolean;        // true while verifying
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthCtx = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Bootstrap: on mount, check token -> /me
  useEffect(() => {
    const init = async () => {
      try {
        const token = getAccessToken();
        if (!token) return;
        const me = await fetchMe(token);
        setUser(me);
      } catch {
        clearTokens();
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { access_token, refresh_token } = await apiLogin(email, password);
      saveTokens(access_token, refresh_token);
      const me = await fetchMe(access_token);
      setUser(me);
      router.replace("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    router.replace("/login");
  };

  const refreshMe = async () => {
    const token = getAccessToken();
    if (!token) throw new Error("No token");
    const me = await fetchMe(token);
    setUser(me);
  };

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshMe }),
    [user, loading]
  );

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
