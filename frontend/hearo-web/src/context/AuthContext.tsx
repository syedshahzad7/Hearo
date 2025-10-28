"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { UserPublic } from "@/lib/auth";
import { apiLogin, fetchMe } from "@/lib/api";
import { getAccessToken, saveTokens, clearTokens } from "@/lib/auth";
import { useRouter } from "next/navigation";

type AuthState = {
  user: UserPublic | null;
  accessToken: string | null;                 // <-- exposed for consumers
  loading: boolean;                           // true while verifying / logging in
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthCtx = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(
    typeof window !== "undefined" ? getAccessToken() : null
  );
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Bootstrap: on mount, if we have a token, fetch /me
  useEffect(() => {
    const init = async () => {
      try {
        if (!accessToken) return;
        const me = await fetchMe(accessToken);
        setUser(me);
      } catch {
        clearTokens();
        setAccessToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { access_token, refresh_token } = await apiLogin(email, password);
      saveTokens(access_token, refresh_token);   // persists to localStorage
      setAccessToken(access_token);
      const me = await fetchMe(access_token);
      setUser(me);
      router.replace("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearTokens();
    setAccessToken(null);
    setUser(null);
    router.replace("/login");
  };

  const refreshMe = async () => {
    if (!accessToken) throw new Error("No token");
    const me = await fetchMe(accessToken);
    setUser(me);
  };

  const value = useMemo(
    () => ({ user, accessToken, loading, login, logout, refreshMe }),
    [user, accessToken, loading]
  );

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
