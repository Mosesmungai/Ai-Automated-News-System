"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const CATEGORIES = ["World", "Africa", "Kenya", "Business", "Technology", "Sports"];

export default function Navbar() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 2) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      setQuery("");
    }
  };

  return (
    <nav className="navbar">
      <div className="container navbar__inner">
        {/* Brand */}
        <Link href="/" className="navbar__brand">
          Kenya<span className="navbar__brand-accent">News</span>
        </Link>

        {/* Links */}
        <div className="navbar__nav">
          {CATEGORIES.map((cat) => (
            <Link key={cat} href={`/category/${cat.toLowerCase()}`} className="navbar__link">
              {cat}
            </Link>
          ))}
        </div>

        {/* Search & Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <form onSubmit={handleSearch} style={{ display: "flex", alignItems: "center", borderBottom: "1px solid var(--text-primary)" }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search..."
              style={{ border: "none", outline: "none", padding: "4px 8px", fontSize: "14px", width: "120px" }}
            />
            <button type="submit" style={{ padding: "4px" }} aria-label="Search">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </button>
          </form>
          <a href="#subscribe" className="btn btn-primary" style={{ padding: "6px 16px", fontSize: "12px" }}>
            Subscribe
          </a>
        </div>
      </div>
    </nav>
  );
}
