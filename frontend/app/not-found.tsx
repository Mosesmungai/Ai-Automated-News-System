import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function NotFound() {
  return (
    <>
      <Navbar />
      <div style={{
        minHeight: "70vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px",
        textAlign: "center",
      }}>
        <div style={{ fontSize: "80px", marginBottom: "16px" }}>📭</div>
        <h1 style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: "48px",
          fontWeight: 800,
          color: "var(--slate-100)",
        }}>
          404
        </h1>
        <p style={{ fontSize: "18px", color: "var(--slate-400)", margin: "12px 0 32px" }}>
          This story couldn't be found. It may have been removed.
        </p>
        <Link href="/" className="btn btn-primary" style={{ fontSize: "15px", padding: "12px 28px" }}>
          ← Back to Home
        </Link>
      </div>
    </>
  );
}
