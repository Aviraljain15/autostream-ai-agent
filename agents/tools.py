"""
agent/tools.py
--------------
Tool definitions for AutoStream agent.
Contains the mock lead capture function and its wrapper.
"""

import re
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# Mock Lead Capture (as specified in requirements)
# ─────────────────────────────────────────────

def mock_lead_capture(name: str, email: str, platform: str) -> dict:
    """
    Mock API call to capture a qualified lead.
    In production, this would POST to a CRM like HubSpot or Salesforce.

    Args:
        name     : Full name of the lead
        email    : Email address of the lead
        platform : Creator platform (YouTube, Instagram, etc.)

    Returns:
        dict with status and lead_id
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lead_id = f"AS-{abs(hash(email)) % 100000:05d}"

    # ── Required print statement as per specification ──
    print(f"\n{'='*55}")
    print(f"  ✅  Lead captured successfully!")
    print(f"{'='*55}")
    print(f"  Name     : {name}")
    print(f"  Email    : {email}")
    print(f"  Platform : {platform}")
    print(f"  Lead ID  : {lead_id}")
    print(f"  Time     : {timestamp}")
    print(f"{'='*55}\n")

    return {
        "status": "success",
        "lead_id": lead_id,
        "name": name,
        "email": email,
        "platform": platform,
        "timestamp": timestamp
    }


# ─────────────────────────────────────────────
# Validation Helpers
# ─────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


KNOWN_PLATFORMS = [
    "youtube", "instagram", "tiktok", "linkedin",
    "twitter", "x", "facebook", "twitch", "snapchat",
    "podcast", "blog", "other"
]

def normalize_platform(raw: str) -> str:
    """Normalize platform string to a clean display name."""
    mapping = {
        "youtube": "YouTube",
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "linkedin": "LinkedIn",
        "twitter": "Twitter/X",
        "x": "Twitter/X",
        "facebook": "Facebook",
        "twitch": "Twitch",
        "snapchat": "Snapchat",
        "podcast": "Podcast",
        "blog": "Blog",
        "other": "Other",
    }
    key = raw.strip().lower()
    return mapping.get(key, raw.strip().title())


def extract_email_from_text(text: str) -> Optional[str]:
    """Extract first email address found in a string."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


# Make Optional importable from this module too
from typing import Optional
