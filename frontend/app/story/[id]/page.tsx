import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getStory, getStories } from "@/lib/api";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Link from "next/link";
import StoryCard from "@/components/StoryCard";

interface Props {
  params: { id: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const story = await getStory(params.id);
    return {
      title: story.headline,
      description: story.summary,
    };
  } catch {
    return { title: "Story not found" };
  }
}

export const revalidate = 60;

export default async function StoryPage({ params }: Props) {
  let story;
  try {
    story = await getStory(params.id);
  } catch {
    notFound();
  }

  const related = await getStories(1, 4, story.category).then(
    (r) => r.stories.filter((s) => s.id !== story.id).slice(0, 3)
  ).catch(() => []);

  const image = story.media?.[0] ?? null;

  return (
    <>
      <Navbar />

      <main className="container" style={{ paddingBottom: "80px" }}>
        
        {/* Article Header (Centered, Clean) */}
        <header className="article-header">
          <Link href={`/category/${story.category.toLowerCase()}`} className="category-tag">
            {story.category}
          </Link>
          <h1 className="headline-serif article-title">{story.headline}</h1>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", alignItems: "center" }}>
            <span className="text-meta">{story.timestamp}</span>
            <span className="text-meta">|</span>
            <span className="text-meta">{story.source}</span>
            {story.social_mentions > 0 && (
              <>
                <span className="text-meta">|</span>
                <span className="text-meta" style={{ color: "var(--brand-primary)" }}>
                  Trending ({story.social_mentions})
                </span>
              </>
            )}
          </div>
        </header>

        {/* Hero Image */}
        {image && (
          <div className="article-hero-wrap">
            <img src={image} alt={story.headline} className="article-hero-img" />
          </div>
        )}

        {/* Article Content */}
        <div className="article-body-wrap">
          
          <div className="article-summary-box">
            <span className="text-meta" style={{ color: "var(--brand-dark)" }}>AI Summary</span>
            <p style={{ marginTop: "8px", fontWeight: 500 }}>{story.summary}</p>
          </div>

          {story.bullets?.length > 0 && (
            <ul className="article-bullets">
              {story.bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          )}

          <div style={{ marginTop: "48px", borderTop: "1px solid var(--border-light)", paddingTop: "24px" }}>
            <span className="text-meta">Sources</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "12px" }}>
              {story.source_links?.map((link, i) => (
                <a key={i} href={link} target="_blank" rel="noopener noreferrer" className="btn btn-outline" style={{ padding: "8px 16px" }}>
                  {story.verified_by[i] ?? `Source ${i + 1}`} ↗
                </a>
              ))}
            </div>
          </div>
        </div>

      </main>
      <Footer />
    </>
  );
}
