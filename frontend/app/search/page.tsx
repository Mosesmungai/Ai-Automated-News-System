"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import { searchStories, type Story } from "@/lib/api";
import StoryCard from "@/components/StoryCard";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

function SearchResults() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const q = searchParams.get("q") ?? "";
  const [query, setQuery]     = useState(q);
  const [results, setResults] = useState<Story[]>([]);
  const [total, setTotal]     = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  useEffect(() => {
    if (!q || q.length < 2) return;
    setLoading(true);
    setError("");
    searchStories(q)
      .then((res) => {
        setResults(res.stories);
        setTotal(res.total);
      })
      .catch(() => setError("Search failed. Is the backend running?"))
      .finally(() => setLoading(false));
  }, [q]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <>
      <Navbar />
      <main>
        {/* Search hero */}
        <div style={{
          background: "linear-gradient(160deg, var(--navy-900), var(--navy-950))",
          borderBottom: "1px solid rgba(255,255,255,.05)",
          padding: "48px 24px",
        }}>
          <div className="container">
            <h1 style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "clamp(24px, 3vw, 32px)",
              fontWeight: 800,
              marginBottom: "24px",
            }}>
              🔍 Search Stories
            </h1>
            <form onSubmit={handleSubmit} style={{ display: "flex", gap: "12px", maxWidth: "560px" }}>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search Kenya, business, elections…"
                style={{
                  flex: 1,
                  background: "var(--slate-800)",
                  border: "1px solid rgba(255,255,255,.1)",
                  borderRadius: "var(--radius-sm)",
                  padding: "12px 20px",
                  color: "var(--slate-100)",
                  fontSize: "16px",
                  outline: "none",
                }}
                aria-label="Search stories"
              />
              <button type="submit" className="btn btn-primary" style={{ padding: "12px 24px" }}>
                Search
              </button>
            </form>
          </div>
        </div>

        {/* Results */}
        <section className="section">
          <div className="container">
            {loading && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "24px" }}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} style={{ borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
                    <div className="skeleton" style={{ height: "200px" }} />
                    <div style={{ padding: "20px", background: "var(--slate-800)", display: "flex", flexDirection: "column", gap: "12px" }}>
                      <div className="skeleton" style={{ height: "14px", width: "40%" }} />
                      <div className="skeleton" style={{ height: "18px" }} />
                      <div className="skeleton" style={{ height: "13px", width: "80%" }} />
                      <div className="skeleton" style={{ height: "13px", width: "60%" }} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div style={{ textAlign: "center", padding: "60px 0", color: "var(--red-400)" }}>
                <div style={{ fontSize: "48px", marginBottom: "12px" }}>⚠️</div>
                <p>{error}</p>
              </div>
            )}

            {!loading && !error && q && results.length === 0 && (
              <div style={{ textAlign: "center", padding: "80px 0", color: "var(--slate-500)" }}>
                <div style={{ fontSize: "64px", marginBottom: "16px" }}>🔍</div>
                <p style={{ fontSize: "18px" }}>No results for "<strong style={{ color: "var(--slate-300)" }}>{q}</strong>"</p>
                <p style={{ fontSize: "14px", marginTop: "8px" }}>Try different keywords.</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
                              marginBottom: "24px" }}>
                  <h2 style={{ fontSize: "18px", fontWeight: 700 }}>
                    Results for "<span style={{ color: "var(--gold-400)" }}>{q}</span>"
                  </h2>
                  <span style={{ fontSize: "13px", color: "var(--slate-500)" }}>{total} found</span>
                </div>
                <div className="grid-stories">
                  {results.map((s) => (
                    <StoryCard key={s.id} story={s} />
                  ))}
                </div>
              </>
            )}

            {!q && !loading && (
              <div style={{ textAlign: "center", padding: "80px 0", color: "var(--slate-500)" }}>
                <div style={{ fontSize: "64px", marginBottom: "16px" }}>📰</div>
                <p style={{ fontSize: "18px" }}>Enter a search term above to find stories.</p>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div style={{ color: "var(--slate-400)", padding: "40px", textAlign: "center" }}>Loading…</div>}>
      <SearchResults />
    </Suspense>
  );
}
