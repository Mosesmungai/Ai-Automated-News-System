import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getByCategory } from "@/lib/api";
import Navbar from "@/components/Navbar";
import StoryCard from "@/components/StoryCard";
import Footer from "@/components/Footer";

interface Props {
  params: { slug: string };
}

const VALID = ["kenya", "africa", "world", "business", "sports", "technology", "health", "politics", "general"];

function toTitle(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const cat = toTitle(params.slug);
  return {
    title: `${cat} News`,
    description: `Latest ${cat} news — AI-verified, updated every 10 minutes.`,
  };
}

export const revalidate = 60;

export default async function CategoryPage({ params }: Props) {
  const { slug } = params;
  if (!VALID.includes(slug.toLowerCase())) notFound();

  const cat = toTitle(slug);
  const data = await getByCategory(cat, 30).catch(() => ({ category: cat, stories: [], count: 0 }));

  return (
    <>
      <Navbar />

      <main>
        {/* Category Header */}
        <div style={{
          borderBottom: "1px solid var(--border-light)",
          padding: "64px 0 48px",
        }}>
          <div className="container" style={{ textAlign: "center" }}>
            <h1 className="headline-serif" style={{ fontSize: "clamp(32px, 5vw, 48px)", marginBottom: "8px" }}>
              {cat}
            </h1>
            <p className="text-meta">
              {data.count} verified stories · updated every 10 minutes
            </p>
          </div>
        </div>

        {/* Stories list */}
        <section className="section">
          <div className="container" style={{ maxWidth: "800px" }}>
            {data.stories.length === 0 ? (
              <div style={{ textAlign: "center", padding: "80px 0", color: "var(--text-tertiary)" }}>
                <p style={{ fontSize: "18px" }}>No {cat} stories yet.</p>
                <p style={{ fontSize: "14px", marginTop: "8px" }}>
                  Check back after the next pipeline run.
                </p>
              </div>
            ) : (
              <div>
                {data.stories.map((s) => (
                  <StoryCard key={s.id} story={s} />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
