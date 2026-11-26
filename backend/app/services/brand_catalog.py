import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache

logger = logging.getLogger("sharkmmo.brands")

# 61 Brands Config matching Canboso layout in latest screenshot (media_1795678770961_bf922967.jpg)
# Structure: (display_name, slug, icon, keywords, emojis)
BRANDS_LAYOUT: List[Tuple[str, str, str, List[str], List[str]]] = [
    # Row 1
    ("Adobe", "adobe", "🟥", ["adobe", "photoshop", "illustrator", "premiere", "acrobat", "lightroom"], ["adobe"]),
    ("Antigravity", "antigravity", "🔺", ["antigravity"], ["antigravity"]),
    ("API Claude", "api_claude", "✴️", ["api claude", "claude api", "build api claude"], []),
    # Row 2
    ("API Codex", "api_codex", "⚙️", ["api codex", "codex api", "codex"], []),
    ("Cursor", "cursor", "📦", ["cursor"], ["cursor"]),
    ("API Deepseek", "api_deepseek", "🐋", ["deepseek", "api deepseek"], []),
    # Row 3
    ("API Gemini", "api_gemini", "✨", ["gemini", "api gemini"], []),
    ("AutoDesk", "autodesk", "🅰️", ["autodesk", "autocad", "3ds max", "revit"], ["autodesk"]),
    ("Canva", "canva", "🎨", ["canva"], ["canva"]),
    # Row 4
    ("Capcut", "capcut", "✂️", ["capcut"], ["capcut"]),
    ("ChatGPT", "chatgpt", "🤖", ["chatgpt", "chat gpt", "gpt-4", "openai", "apigpt"], ["chatgpt", "apigpt"]),
    ("Dreamina", "dreamina", "✈️", ["dreamina"], ["dreamina"]),
    # Row 5
    ("Duolingo", "duolingo", "🦉", ["duolingo"], ["duolingo"]),
    ("ElevenLabs", "elevenlabs", "🎙️", ["elevenlabs", "eleven labs", "eleven"], ["elevenlabs"]),
    ("Facebook", "facebook", "📘", ["facebook", "fb "], ["facebook"]),
    # Row 6
    ("Figma", "figma", "🎨", ["figma"], ["figma"]),
    ("Gamma", "gamma", "🇬", ["gamma"], ["gamma"]),
    ("Gmail", "gmail", "✉️", ["gmail", "google mail"], ["gmail"]),
    # Row 7
    ("GPM", "gpm", "🖥️", ["gpm", "gpm login", "gpm-login"], ["gpm_login"]),
    ("Grok", "grok", "⚡", ["grok"], ["grok"]),
    ("HeyGen", "heygen", "👤", ["heygen"], ["heygen"]),
    # Row 8
    ("Higgsfield", "higgsfield", "🟩", ["higgsfield", "higgfield"], ["higgfield"]),
    ("Kling", "kling", "🎬", ["kling"], ["kling"]),
    ("Krea", "krea", "⚫", ["krea"], ["krea"]),
    # Row 9
    ("Locket", "locket", "💛", ["locket"], ["locket"]),
    ("Lovable", "lovable", "💖", ["lovable"], ["lovable"]),
    ("Manus", "manus", "🦾", ["manus"], ["manus"]),
    # Row 10
    ("MB Bank", "mb_bank", "🏦", ["mb bank", "mbbank"], ["mb"]),
    ("Meitu", "meitu", "🌸", ["meitu"], ["meitu"]),
    ("Microsoft 365", "microsoft_365", "💼", ["microsoft", "office 365", "office", "windows", "ms365", "word", "excel"], ["microsoft_office_365", "windows"]),
    # Row 11
    ("Minimax", "minimax", "⚡", ["minimax"], ["minimax"]),
    ("Notion", "notion", "📝", ["notion"], ["notion"]),
    ("Zoom", "zoom", "📹", ["zoom"], ["zoom"]),
    # Row 12
    ("OpenArt", "openart", "🎨", ["openart"], ["openart"]),
    ("Outlook", "outlook", "📧", ["outlook", "hotmail"], ["outlook"]),
    ("Quizlet", "quizlet", "🔤", ["quizlet"], ["quizlet"]),
    # Row 13
    ("Qwen", "qwen", "🟣", ["qwen"], []),
    ("Runway", "runway", "🎞️", ["runway"], ["runway"]),
    ("Spotify", "spotify", "🟢", ["spotify"], ["spotify"]),
    # Row 14
    ("VPN & Proxy", "vpn_proxy", "🛡️", [
        "vpn", "proxy", "nordvpn", "hma", "surfshark", "express", "adguard",
        "hotspot", "purevpn", "norton", "proton", "kaspersky"
    ], [
        "nordvpn", "hma_vpn", "surfshark", "express", "adguard_vpn",
        "hotspot_shield", "purevpn", "norton_vpn", "proton", "kaspersky"
    ]),
    ("Xingtu", "xingtu", "📷", ["xingtu"], ["xingtu"]),
    ("Youtube", "youtube", "🔴", ["youtube", "vidiq"], ["youtube"]),
    # Row 15
    ("Muse AI", "muse_ai", "🎼", ["muse", "muse ai"], ["muse_ai"]),
    ("linkedin", "linkedin", "💼", ["linkedin"], ["linkedin"]),
    ("Google One", "google_one", "1️⃣", ["google one", "drive 2tb"], ["google_one"]),
    # Row 16
    ("NetFlix", "netflix", "🍿", ["netflix"], ["netflix"]),
    ("Replit", "replit", "🌀", ["replit"], ["replit"]),
    ("Alight Motion", "alight_motion", "💫", ["alight motion", "alight"], ["alight_motion"]),
    # Row 17
    ("Wispr Flow", "wispr_flow", "🌬️", ["wispr flow", "wispr"], ["wispr_flow"]),
    ("Tool Veo3", "tool_veo3", "✦", ["tool veo3", "veo 3", "veo3", "veo"], []),
    ("Amazon Prime", "amazon_prime", "📦", ["amazon prime", "amazon", "prime video"], ["amazon_prime"]),
    # Row 18
    ("Tele", "tele", "✈️", ["tele", "telegram"], ["tele"]),
    ("GenSpark", "genspark", "✨", ["genspark"], ["genspark"]),
    ("Framer", "framer", "📐", ["framer"], ["framer"]),
    # Row 19
    ("Leonardo AI", "leonardo_ai", "🎨", ["leonardo"], ["leonardo_ai"]),
    ("Pippit AI", "pippit_ai", "🐣", ["pippit", "pipit", "pitpit"], ["pippit_ai"]),
    ("Freepik", "freepik", "👑", ["freepik", "flaticon"], ["freepik"]),
    # Row 20
    ("Picsart", "picsart", "🟣", ["picsart"], ["picsart"]),
    ("SCRIBD", "scribd", "📖", ["scribd"], ["scribd"]),
    ("Seedance", "seedance", "🌱", ["seedance"], ["seedance"]),
    # Row 21
    ("Claude Official", "claude_official", "✴️", ["claude pro", "claude max", "claude official", "claude 3", "claude x5", "claude"], ["claude"]),
]

BRANDS_DICT: Dict[str, Dict[str, Any]] = {
    slug: {
        "name": name,
        "slug": slug,
        "icon": icon,
        "keywords": kws,
        "emojis": emojis
    }
    for name, slug, icon, kws, emojis in BRANDS_LAYOUT
}


EMOJI_BRAND_MAP = {
    "antigravity": "antigravity",
    "chatgpt": "chatgpt",
    "apigpt": "api_codex",
    "kling": "kling",
    "youtube": "youtube",
    "gmail": "gmail",
    "higgfield": "higgsfield",
    "dreamina": "dreamina",
    "grok": "grok",
    "canva": "canva",
    "muse_ai": "muse_ai",
    "adobe": "adobe",
    "meitu": "meitu",
    "microsoft_office_365": "microsoft_365",
    "windows": "microsoft_365",
    "notion": "notion",
    "capcut": "capcut",
    "google_one": "google_one",
    "gamma": "gamma",
    "zoom": "zoom",
    "express": "vpn_proxy",
    "nordvpn": "vpn_proxy",
    "hma_vpn": "vpn_proxy",
    "surfshark": "vpn_proxy",
    "adguard_vpn": "vpn_proxy",
    "hotspot_shield": "vpn_proxy",
    "purevpn": "vpn_proxy",
    "norton_vpn": "vpn_proxy",
    "proton": "vpn_proxy",
    "kaspersky": "vpn_proxy",
    "heygen": "heygen",
    "cursor": "cursor",
    "wink": "wink",
    "minimax": "minimax",
    "spotify": "spotify",
    "elevenlabs": "elevenlabs",
    "duolingo": "duolingo",
    "perplexity": "perplexity",
    "autodesk": "autodesk",
    "facebook": "facebook",
    "runway": "runway",
    "openart": "openart",
    "suno": "suno",
    "xingtu": "xingtu",
    "figma": "figma",
    "gpm_login": "gpm",
    "quizlet": "quizlet",
    "lovable": "lovable",
    "locket": "locket",
    "outlook": "outlook",
    "leonardo_ai": "leonardo_ai",
    "linkedin": "linkedin",
    "netflix": "netflix",
    "jetbrains": "jetbrains",
    "mb": "mb_bank",
    "manus": "manus",
    "replit": "replit",
    "tryclico": "clico",
    "alight_motion": "alight_motion",
    "zed": "zed",
    "wispr_flow": "wispr_flow",
    "framer": "framer",
    "genspark": "genspark",
    "amazon_prime": "amazon_prime",
    "pippit_ai": "pippit_ai",
    "krea": "krea",
    "tele": "tele",
    "freepik": "freepik",
    "picsart": "picsart",
    "scribd": "scribd",
    "seedance": "seedance",
}


def match_product_to_brand(name: str, emoji: Optional[str] = None) -> str:
    """Finds the most specific brand slug for a product."""
    n = name.lower()
    em = (emoji or "").lower()

    # 1. Direct authoritative emoji from Canboso:
    if em:
        if em == "claude":
            if "api claude" in n or "build api" in n:
                return "api_claude"
            return "claude_official"
        if em in EMOJI_BRAND_MAP:
            return EMOJI_BRAND_MAP[em]

    # 2. Priority compound brands for products with none emoji
    priority_slugs = ["flow_veo3", "api_claude", "api_codex", "api_deepseek", "api_gemini", "tool_veo3"]
    for slug in priority_slugs:
        meta = BRANDS_DICT[slug]
        if any(kw in n for kw in meta["keywords"]):
            return slug

    # 3. Match by keywords
    for slug, meta in BRANDS_DICT.items():
        if any(kw in n for kw in meta["keywords"]):
            return slug

    return "other"


def get_brand_filter_condition(slug: str):
    """Generates an SQLAlchemy OR condition to filter products belonging to a brand."""
    meta = BRANDS_DICT.get(slug)
    if not meta:
        return None

    conditions = []
    # Emojis filter
    for em in meta["emojis"]:
        conditions.append(ProductCache.emoji.ilike(f"%{em}%"))

    # Keywords filter on name and description
    for kw in meta["keywords"]:
        conditions.append(ProductCache.name.ilike(f"%{kw}%"))

    return or_(*conditions) if conditions else None


async def get_brand_products(
    session: AsyncSession,
    slug: str,
    page: int = 1,
    page_size: int = 15
) -> Tuple[List[ProductCache], int, int]:
    """Returns products for a given brand with pagination."""
    base_q = select(ProductCache).where(ProductCache.is_active == True)
    count_q = select(func.count(ProductCache.id)).where(ProductCache.is_active == True)

    # Cross-brand custom filtering so all relevant products are accessible
    if slug == "antigravity":
        cond = or_(
            ProductCache.brand_slug == "antigravity",
            ProductCache.emoji == "antigravity",
            ProductCache.name.ilike("%antigravity%"),
            ProductCache.name.ilike("%admin ultra%"),
            ProductCache.name.ilike("%google ultra%")
        )
    elif slug == "flow_veo3":
        cond = or_(
            ProductCache.brand_slug == "flow_veo3",
            ProductCache.name.ilike("%veo3 ultra%"),
            ProductCache.name.ilike("%google flow%"),
            ProductCache.name.ilike("%admin ultra%")
        )
    elif slug == "tool_veo3":
        cond = or_(
            ProductCache.brand_slug == "tool_veo3",
            ProductCache.name.ilike("%veo3%"),
            ProductCache.name.ilike("%veo 3%")
        )
    elif slug == "api_gemini":
        cond = or_(
            ProductCache.brand_slug == "api_gemini",
            ProductCache.name.ilike("%gemini%")
        )
    elif slug == "api_claude":
        cond = or_(
            ProductCache.brand_slug == "api_claude",
            ProductCache.name.ilike("%api claude%"),
            ProductCache.name.ilike("%build api%")
        )
    elif slug == "claude_official":
        cond = or_(
            ProductCache.brand_slug == "claude_official",
            (ProductCache.name.ilike("%claude%") & ~ProductCache.name.ilike("%api claude%"))
        )
    elif slug == "chatgpt":
        cond = or_(
            ProductCache.brand_slug == "chatgpt",
            ProductCache.name.ilike("%chatgpt%"),
            ProductCache.name.ilike("%chat gpt%")
        )
    else:
        brand_cond = (ProductCache.brand_slug == slug)
        keyword_cond = get_brand_filter_condition(slug)
        cond = or_(brand_cond, keyword_cond) if keyword_cond is not None else brand_cond

    base_q = base_q.where(cond)
    count_q = count_q.where(cond)
    total_count = (await session.execute(count_q)).scalar() or 0

    # In-stock products first, high availability first
    in_stock_order = case((ProductCache.available_qty > 0, 0), else_=1)
    if slug == "antigravity":
        is_ultra_order = case((ProductCache.name.ilike('%ultra%') | ProductCache.name.ilike('%antigravity%'), 0), else_=1)
        base_q = base_q.order_by(
            in_stock_order,
            is_ultra_order,
            ProductCache.available_qty.desc(),
            ProductCache.sold_qty.desc(),
            ProductCache.id.asc()
        )
    else:
        base_q = base_q.order_by(
            in_stock_order,
            ProductCache.available_qty.desc(),
            ProductCache.sold_qty.desc(),
            ProductCache.id.asc()
        )
    total_pages = max(1, math.ceil(total_count / page_size))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * page_size
    items_res = await session.execute(base_q.offset(offset).limit(page_size))
    products = items_res.scalars().all()

    return products, total_count, total_pages


HOT_FEATURED_PATTERNS = [
    "%Admin Ultra x20 + Veo3 Ultra 25K Credits 1 tháng BHF%",
    "%Kling Team 20K Credits 1 tháng BH 2 ngày%",
    "%ChatGPT Plus 1 tháng BH 1 ngày%",
    "%ChatGPT Plus 1 tháng BHF%",
    "%Higgsfield Ultra 9K Credits 1 tháng BH 1 ngày%",
    "%Build API Claude theo yêu cầu 1 tháng BHF%"
]


async def get_featured_store_products(
    session: AsyncSession,
    limit: int = 7
) -> List[ProductCache]:
    """
    Returns the top featured / hot products matching Canboso's featured shelf:
    Admin Ultra, Kling, ChatGPT Plus, Higgsfield, Build API Claude, etc.
    """
    featured = []
    seen_ids = set()

    # 1. Exact match the hot items in Canboso layout
    for pat in HOT_FEATURED_PATTERNS:
        q = (
            select(ProductCache)
            .where(ProductCache.name.ilike(pat), ProductCache.is_active == True)
            .limit(1)
        )
        res = await session.execute(q)
        p = res.scalars().first()
        if p and p.product_id not in seen_ids:
            featured.append(p)
            seen_ids.add(p.product_id)

    # 2. Fill any remaining slots with highest available quantity
    if len(featured) < limit:
        remaining = limit - len(featured)
        in_stock_order = case((ProductCache.available_qty > 0, 0), else_=1)
        q = (
            select(ProductCache)
            .where(
                ProductCache.is_active == True,
                ProductCache.product_id.not_in(list(seen_ids)) if seen_ids else True
            )
            .order_by(
                in_stock_order,
                ProductCache.available_qty.desc(),
                ProductCache.sold_qty.desc()
            )
            .limit(remaining)
        )
        res = await session.execute(q)
        for p in res.scalars().all():
            if p.product_id not in seen_ids:
                featured.append(p)
                seen_ids.add(p.product_id)

    return featured[:limit]
