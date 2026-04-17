import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "KenyaNews — Automated Kenyan & African News",
    template: "%s | KenyaNews",
  },
  description:
    "Real-time, AI-verified Kenyan and African news. Updated every 10 minutes from trusted sources including Standard Media, Nation Africa, BBC Africa, and more.",
  keywords: ["Kenya news", "Africa news", "breaking news Kenya", "Nairobi", "KenyaNews"],
  openGraph: {
    type: "website",
    locale: "en_KE",
    siteName: "KenyaNews",
    title: "KenyaNews — Automated Kenyan & African News",
    description: "Real-time AI-verified Kenyan and African news, updated every 10 minutes.",
  },
  twitter: {
    card: "summary_large_image",
    title: "KenyaNews",
    description: "Real-time AI-verified Kenyan news, updated every 10 minutes.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="theme-color" content="#050d1a" />
      </head>
      <body>{children}</body>
    </html>
  );
}
