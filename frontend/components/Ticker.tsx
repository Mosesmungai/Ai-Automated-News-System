"use client";

import { useEffect, useState } from "react";
import type { Story } from "@/lib/api";

export default function Ticker({ stories }: { stories: Story[] }) {
  const [items, setItems] = useState<Story[]>([]);
  useEffect(() => setItems([...stories, ...stories]), [stories]);

  if (!stories.length) return null;

  return (
    <div className="ticker-wrap">
      <span className="ticker-label">LATEST</span>
      <span className="ticker-track">
        {items.map((s, i) => (
          <a key={`${s.id}-${i}`} href={`/story/${s.id}`} className="ticker-item">
            <span>{s.headline}</span>
            <span className="ticker-divider" />
          </a>
        ))}
      </span>
    </div>
  );
}
