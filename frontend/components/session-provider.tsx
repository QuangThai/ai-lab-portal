"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type UserSession = {
  user: {
    id: string;
    name: string;
    email: string;
    image?: string | null;
  };
} | null;

type SessionContextValue = {
  session: UserSession;
  /** True only while the initial fetch is in-flight (first mount). */
  loading: boolean;
  /** Force a re-fetch, e.g. after sign-in / sign-out. */
  refresh: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within <SessionProvider>");
  return ctx;
}

/**
 * Fetches the current user session exactly once (on first mount) and caches it.
 * Place this high in the tree (e.g. root layout) so it survives page navigations.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<UserSession>(null);
  const [loading, setLoading] = useState(true);

  const fetchSession = async () => {
    try {
      const res = await fetch("/api/auth/get-session");
      if (res.ok) {
        const data: UserSession = await res.json();
        setSession(data);
      } else {
        setSession(null);
      }
    } catch {
      setSession(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, []);

  return (
    <SessionContext.Provider value={{ session, loading, refresh: fetchSession }}>
      {children}
    </SessionContext.Provider>
  );
}
