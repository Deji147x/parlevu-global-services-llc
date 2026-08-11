"""Generate short-form video scripts from blog posts for social media (TikTok/Reels).

Extracts key points, creates 30-60 sec talking points, generates text overlay prompts.

Usage:
  python tools/generate_video_script.py <slug> "<post_title>"
"""
import sys
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Video script templates
VIDEO_TYPES = {
    "quick_tip": {
        "duration": "15-30 sec",
        "format": "Text overlay + visual",
        "structure": ["Hook (3 sec)", "Tip (10 sec)", "CTA (5 sec)"]
    },
    "faq_answer": {
        "duration": "45-60 sec",
        "format": "Talking head or voiceover",
        "structure": ["Question (5 sec)", "Answer (40 sec)", "CTA (5 sec)"]
    },
    "story": {
        "duration": "60-90 sec",
        "format": "Narrative + visuals",
        "structure": ["Hook (5 sec)", "Story (50 sec)", "Resolution (10 sec)", "CTA (5 sec)"]
    }
}

def generate_script(slug, title, video_type="quick_tip"):
    """Generate video script for a blog post."""

    scripts = {
        "sell-my-house-fast-newport-news": {
            "quick_tip": {
                "hook": "Need to sell fast? ⏰",
                "tip": "Cash buyers can close in 7-14 days. No repairs, no waiting. That's how homeowners in Newport News are getting offers in 24 hours.",
                "cta": "Get your free cash offer →",
                "overlay_text": "7-14 Day Closing | No Repairs | Fair Offer in 24 Hours",
                "hashtags": "#CashBuyer #RealEstate #FastSale"
            },
            "faq_answer": {
                "question": "How fast can I really sell my house?",
                "answer": "With a cash buyer, most sales close in 7-21 days from the first phone call. You pick the closing date — we've closed in under a week when a seller needed it.",
                "cta": "Schedule your free consultation",
                "visual_cues": ["Clock ticking", "Calendar flip", "Handshake", "Keys exchange"]
            }
        },
        "sell-my-house-fast-woodridge": {
            "quick_tip": {
                "hook": "Stuck in a slow market? 🏠",
                "tip": "Woodridge homeowners are selling fast with cash offers. No open houses, no showings, no repairs. Get your offer in 24 hours.",
                "cta": "Get a cash offer today",
                "overlay_text": "Woodridge DC | Sell Fast | No Repairs Required",
                "hashtags": "#DCRealEstate #CashOffer #HomeSale"
            }
        },
        "how-cash-buyers-work-md": {
            "quick_tip": {
                "hook": "How do cash buyers actually work? 💰",
                "tip": "We evaluate your home, make a fair offer in 24 hours, and close in 7-14 days. No appraisals, no financing contingencies, no delays.",
                "cta": "Learn how we buy homes",
                "overlay_text": "Cash Buyer Process | Fair Offer | Fast Close",
                "hashtags": "#RealEstate #CashBuyer #Maryland"
            },
            "story": {
                "hook": "Sarah inherited a property. She needed to sell fast.",
                "story": "She was stressed about managing a home 3 states away. Traditional agents said 60-90 days. We made a cash offer in 24 hours. She closed in 10 days and solved her problem.",
                "resolution": "That's what happens when you have options.",
                "cta": "Your story could be next",
                "visual_cues": ["Stressed homeowner", "Phone call", "Offer letter", "Closed sign"]
            }
        }
    }

    if slug not in scripts:
        print(f"No script template for {slug}. Creating default...")
        return {
            "slug": slug,
            "title": title,
            "type": video_type,
            "status": "needs_custom_script",
            "template": VIDEO_TYPES[video_type]
        }

    script = scripts[slug].get(video_type, {})
    return {
        "slug": slug,
        "title": title,
        "video_type": video_type,
        "duration": VIDEO_TYPES[video_type]["duration"],
        "format": VIDEO_TYPES[video_type]["format"],
        "script": script,
        "platforms": ["instagram_reels", "tiktok", "facebook"],
        "posting_times": {
            "instagram": "Monday 8 AM + Wednesday 5 PM",
            "tiktok": "Tuesday 7 PM + Friday 8 AM",
            "facebook": "Thursday 10 AM"
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_video_script.py <slug> [video_type]")
        print("Types: quick_tip, faq_answer, story")
        return

    slug = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else slug.replace("-", " ").title()
    video_type = sys.argv[3] if len(sys.argv) > 3 else "quick_tip"

    script = generate_script(slug, title, video_type)
    print(json.dumps(script, indent=2))

if __name__ == "__main__":
    main()
