"use client";

import AuthGate from "@/components/AuthGate";

export default function WatchPage() {
  return (
    <AuthGate>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Watch</h1>
          <p className="text-sm text-muted-foreground">Not built yet</p>
        </div>
      </div>
    </AuthGate>
  );
}
