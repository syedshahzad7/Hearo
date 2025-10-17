"use client";

import { useEffect, useState } from "react";

export default function HealthCheck() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/health`;
    fetch(url)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="p-4 rounded-xl border">
      <h2 className="text-xl font-semibold mb-2">Backend Health</h2>
      {err && <p className="text-red-600">Error: {err}</p>}
      {data ? (
        <pre className="text-sm">{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p>Loading…</p>
      )}
    </div>
  );
}
