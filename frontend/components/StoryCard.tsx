"use client";

import Link from "next/link";
import type { Story } from "@/lib/api";
import { relativeTime } from "@/lib/api";

interface StoryCardProps {
  story: Story;
  variant?: "horizontal" | "compact" | "hero-center";
}

export default function StoryCard({ story, variant = "horizontal" }: StoryCardProps) {
  const image = story.media?.[0] ?? null;
  const timeAgo = relativeTime(story.timestamp);

  // Center large hero image block
  if (variant === "hero-center") {
    return (
      <Link href={`/story/${story.id}`} className="story-hero-center">
        {image ? (
          <img src={image} alt={story.headline} className="story-hero-center__img" />
        ) : (
          <div className="story-hero-center__img" />
        )}
      </Link>
    );
  }

  // Compact block (right sidebar logic)
  if (variant === "compact") {
    return (
      <Link href={`/story/${story.id}`} className="story-compact">
        <h3 className="story-compact__headline">{story.headline}</h3>
        <span className="text-meta">{timeAgo}</span>
      </Link>
    );
  }

  // Default wide horizontal block
  return (
    <Link href={`/story/${story.id}`} className="story-h">
      {image && (
        <div className="story-h__img-wrap">
          <img src={image} alt={story.headline} className="story-h__img" />
        </div>
      )}
      <div className="story-h__content">
        <span className="category-tag">{story.category}</span>
        <h3 className="story-h__headline">{story.headline}</h3>
        <p className="story-h__summary">{story.summary}</p>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span className="text-meta">{timeAgo}</span>
          <span className="text-meta" style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--brand-dark)" }}>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path d="M5 13l4 4L19 7"></path></svg>
            Verified
          </span>
        </div>
      </div>
    </Link>
  );
}
