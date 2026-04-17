"""
KenyaNews — notifier.py
Sends an HTML email digest via Gmail SMTP every pipeline run.
Recipients are comma-separated in the NOTIFICATION_RECIPIENTS env var.
"""

import os
import requests
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RESEND_API_KEY    = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "KenyaNews <onboarding@resend.dev>")
RECIPIENTS_RAW    = os.getenv("NOTIFICATION_RECIPIENTS", "")
SITE_URL          = os.getenv("FRONTEND_URL", "https://kenya-news.vercel.app")


# ─────────────────────────────────────────
# HTML email builder
# ─────────────────────────────────────────

def build_html(stories: list[dict]) -> str:
    run_time = datetime.now(timezone.utc).strftime("%A, %d %B %Y · %H:%M UTC")

    stories_html = ""
    for i, s in enumerate(stories[:10], 1):          # max 10 in digest
        image_block = ""
        if s.get("media"):
            for m in s["media"]:
                if m and (m.endswith(".jpg") or m.endswith(".png") or
                          m.endswith(".jpeg") or m.endswith(".webp") or
                          "image" in m):
                    image_block = f"""
                        <img src="{m}" alt="story image"
                             style="width:100%;border-radius:8px;margin-bottom:12px;
                                    max-height:220px;object-fit:cover;" />"""
                    break

        bullets_html = ""
        for b in (s.get("bullets") or [s.get("summary", "")])[:3]:
            bullets_html += f"<li style='margin-bottom:6px;'>{b}</li>"

        sources_html = " · ".join(
            f"<a href='{l}' style='color:#F59E0B;text-decoration:none;'>{s.get('source','Source')}</a>"
            for l in (s.get("source_links") or [s.get("link", "#")])[:2]
        )

        stories_html += f"""
        <div style="background:#1e293b;border-radius:12px;padding:24px;
                    margin-bottom:20px;border-left:4px solid #F59E0B;">
            {image_block}
            <span style="background:#F59E0B;color:#0f172a;font-size:11px;
                         font-weight:700;padding:3px 10px;border-radius:20px;
                         text-transform:uppercase;letter-spacing:1px;">
                {s.get('category','General')}
            </span>
            <h2 style="color:#f1f5f9;font-size:18px;margin:12px 0 8px;
                       line-height:1.4;font-family:Georgia,serif;">
                {s['headline']}
            </h2>
            <ul style="color:#94a3b8;font-size:14px;line-height:1.7;
                       padding-left:18px;margin:0 0 14px;">
                {bullets_html}
            </ul>
            <div style="font-size:12px;color:#64748b;">
                🕐 {s.get('timestamp','')} &nbsp;|&nbsp;
                🔗 {sources_html}
                &nbsp;|&nbsp;
                ✅ Verified by {s.get('source_count',1)} sources
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KenyaNews Digest</title></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:Inter,Arial,sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:20px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e40af,#7c3aed);
                border-radius:16px;padding:32px;text-align:center;margin-bottom:24px;">
      <h1 style="color:#fff;margin:0 0 8px;font-size:28px;font-weight:800;
                 letter-spacing:-0.5px;">🇰🇪 KenyaNews</h1>
      <p style="color:#bfdbfe;margin:0;font-size:14px;">
        Automated News Digest · {run_time}
      </p>
      <a href="{SITE_URL}" style="display:inline-block;margin-top:16px;
         background:#F59E0B;color:#0f172a;padding:10px 24px;border-radius:8px;
         font-weight:700;font-size:13px;text-decoration:none;">
        View Full Site →
      </a>
    </div>

    <!-- Summary bar -->
    <div style="background:#1e293b;border-radius:10px;padding:16px 24px;
                margin-bottom:24px;display:flex;align-items:center;">
      <p style="color:#94a3b8;margin:0;font-size:13px;">
        📰 <strong style="color:#f1f5f9;">{len(stories)}</strong> verified stories
        this run &nbsp;·&nbsp;
        🔄 Updates every <strong style="color:#f1f5f9;">10 minutes</strong>
      </p>
    </div>

    <!-- Stories -->
    {stories_html}

    <!-- Footer -->
    <div style="text-align:center;padding:24px 0;color:#475569;font-size:12px;">
      <p>You're receiving this because you subscribed to KenyaNews alerts.</p>
      <p>
        <a href="{SITE_URL}" style="color:#F59E0B;">Visit Website</a>
        &nbsp;·&nbsp;
        Powered by GitHub Actions + Hugging Face + MongoDB Atlas
      </p>
    </div>
  </div>
</body>
</html>"""


# ─────────────────────────────────────────
# Send email
# ─────────────────────────────────────────

def send_digest(stories: list[dict]) -> bool:
    """Send the HTML digest to all NOTIFICATION_RECIPIENTS via Resend API."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email notification.")
        return False

    recipients = [r.strip() for r in RECIPIENTS_RAW.split(",") if r.strip()]
    if not recipients:
        logger.warning("No recipients configured — skipping email notification.")
        return False

    subject = (
        f"🇰🇪 KenyaNews Digest — {len(stories)} stories "
        f"· {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M')} UTC"
    )

    plain = "\n\n".join(
        f"{s['headline']}\n{s.get('summary','')}\n{s.get('link','')}"
        for s in stories[:10]
    )
    html_content = build_html(stories)

    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "text": plain,
        "html": html_content
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"✉ Digest sent to {len(recipients)} recipient(s) via Resend. (ID: {response.json().get('id')})")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email via Resend API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Quick test with dummy story
    test = [{
        "headline": "Kenya Economy Grows by 5 Percent in Q1 2024",
        "summary": "Kenya's GDP grew 5% in Q1 2024 per World Bank data.",
        "bullets": ["GDP grew 5%", "World Bank confirmed the data."],
        "category": "Business",
        "source": "Standard Media",
        "source_links": ["https://standardmedia.co.ke/1"],
        "link": "https://standardmedia.co.ke/1",
        "media": [],
        "timestamp": "2024-06-01 10:00",
        "source_count": 3,
        "verified_sources": ["Standard Media", "BBC Africa", "KNA"],
    }]
    send_digest(test)
