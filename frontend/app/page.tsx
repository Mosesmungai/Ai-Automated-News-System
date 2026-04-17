import type { Metadata } from "next";
import { getStories, getStats } from "@/lib/api";
import Navbar from "@/components/Navbar";
import StoryCard from "@/components/StoryCard";
import Ticker from "@/components/Ticker";
import StatsBar from "@/components/StatsBar";
import Footer from "@/components/Footer";
import Link from "next/link";

export const metadata: Metadata = {
  title: "KenyaNews — The Source for Verified News",
  description: "AI-verified, strictly unbiased Kenyan and global news updated every 10 minutes.",
};

export const revalidate = 60;

export default async function HomePage() {
  const [latestRes, statsRes] = await Promise.allSettled([
    getStories(1, 30),
    getStats(),
  ]);

  const stories = latestRes.status === "fulfilled" ? latestRes.value.stories : [];
  const stats = statsRes.status === "fulfilled" ? statsRes.value : null;

  const topStory = stories[0] ?? null;
  const trendingStories = stories.slice(1, 6);
  const feedStories = stories.slice(6);

  return (
    <>
      <Navbar />
      <Ticker stories={stories.slice(0, 10)} />
      <StatsBar stats={stats} />

      {/* ── Reuters-Style Hero Split ─────────────────────────── */}
      {topStory && (
        <section className="container">
          <div className="hero-split">
            {/* Left Column: Top Story Text */}
            <div className="hero-col-left">
              <span className="category-tag accent" style={{ marginTop: "8px" }}>TOP STORY</span>
              <Link href={`/story/${topStory.id}`}>
                <h1 className="headline-serif top-story-headline">{topStory.headline}</h1>
                <p className="top-story-summary">{topStory.summary}</p>
                <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                  <span className="text-meta">{topStory.timestamp}</span>
                  <span className="text-meta" style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--brand-dark)" }}>
                    <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path d="M5 13l4 4L19 7"></path></svg>
                    Multi-source
                  </span>
                </div>
              </Link>
            </div>

            {/* Center Column: Top Story Media */}
            <div className="hero-col-center">
              <StoryCard story={topStory} variant="hero-center" />
            </div>

            {/* Right Column: Trending / Latest */}
            <div className="hero-col-right">
               <div className="section-header">Trending Now</div>
               {trendingStories.map(s => (
                 <StoryCard key={s.id} story={s} variant="compact" />
               ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Standard Feed ──────────────────────────── */}
      {feedStories.length > 0 && (
        <section className="section">
          <div className="container">
            <div style={{ maxWidth: "800px" }}>
              <div className="section-header">Latest News</div>
              <div>
                {feedStories.map(s => (
                  <StoryCard key={s.id} story={s} />
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      <Footer />
    </>
  );
}
