"use client";

import { useState } from "react";
import Link from "next/link";
import { subscribe } from "@/lib/api";

const CATEGORIES = ["Kenya", "Africa", "World", "Business", "Sports", "Technology"];

export default function Footer() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    setStatus("loading");
    try {
      await subscribe(email);
      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
    }
  };

  return (
    <footer className="footer">
      <div className="container footer__grid">
        
        {/* Brand & Subscribe */}
        <div>
          <div className="navbar__brand" style={{ marginBottom: "16px" }}>
            Kenya<span className="navbar__brand-accent">News</span>
          </div>
          <p style={{ fontSize: "14px", color: "var(--text-secondary)", marginBottom: "24px", maxWidth: "300px" }}>
            Real-time, impartial summaries built from trusted sources, continuously verified.
          </p>
          <form onSubmit={handleSubscribe}>
            <input 
              type="email" 
              className="subscribe-input" 
              placeholder="Sign up for the digest" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={status === "loading"}>
              {status === "loading" ? "Subscribing..." : "Subscribe"}
            </button>
            {status === "success" && <p style={{ fontSize: "12px", color: "var(--brand-dark)", marginTop: "8px" }}>Subscribed.</p>}
          </form>
        </div>

        {/* Links */}
        <div>
          <h4 className="footer__heading">Sections</h4>
          <div className="footer__links">
            {CATEGORIES.map(c => <Link key={c} href={`/category/${c.toLowerCase()}`}>{c}</Link>)}
          </div>
        </div>

        {/* Sources */}
        <div>
          <h4 className="footer__heading">Primary Sources</h4>
          <div className="footer__links">
            <a href="https://standardmedia.co.ke">The Standard</a>
            <a href="https://nation.africa">Nation Africa</a>
            <a href="https://citizen.digital">Citizen Digital</a>
            <a href="https://bbc.com/news/africa">BBC Africa</a>
            <a href="https://reuters.com">Reuters</a>
          </div>
        </div>

        {/* About */}
        <div>
          <h4 className="footer__heading">Company</h4>
          <div className="footer__links">
            <Link href="/">About Us</Link>
            <Link href="/search">Search Portal</Link>
            <span style={{ fontSize: "12px", color: "var(--text-tertiary)", marginTop: "12px", display: "block" }}>
              © {new Date().getFullYear()} KenyaNews
            </span>
          </div>
        </div>

      </div>
    </footer>
  );
}
