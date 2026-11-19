import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache

logger = logging.getLogger("sharkmmo.brands")

# 62 Brands Config matching Canboso layout in Image 3
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
    ("Locket", "locket", "💛", ["locket"], ["locket"]),
    # Row 9
    ("Lovable", "lovable", "💖", ["lovable"], ["lovable"]),
    ("Manus", "manus", "🦾", ["manus"], ["manus"]),
    ("MB Bank", "mb_bank", "🏦", ["mb bank", "mbbank"], ["mb"]),
    # Row 10
    ("Meitu", "meitu", "🌸", ["meitu"], ["meitu"]),
    ("Microsoft 365", "microsoft_365", "💼", ["microsoft", "office 365", "office", "windows", "ms365", "word", "excel"], ["microsoft_office_365", "windows"]),
    ("Minimax", "minimax", "⚡", ["minimax"], ["minimax"]),
    # Row 11
    ("Notion", "notion", "📝", ["notion"], ["notion"]),
    ("Zoom", "zoom", "📹", ["zoom"], ["zoom"]),
    ("OpenArt", "openart", "🎨", ["openart"], ["openart"]),
    # Row 12
    ("Outlook", "outlook", "📧", ["outlook", "hotmail"], ["outlook"]),
    ("Perplexity", "perplexity", "🔍", ["perplexity"], ["perplexity"]),
    ("Quizlet", "quizlet", "🔤", ["quizlet"], ["quizlet"]),
    # Row 13
    ("Qwen", "qwen", "🟣", ["qwen"], []),
    ("Runway", "runway", "🎞️", ["runway"], ["runway"]),
    ("Spotify", "spotify", "🟢", ["spotify"], ["spotify"]),
    # Row 14
    ("Suno", "suno", "🎵", ["suno"], ["suno"]),
    ("VPN & Proxy", "vpn_proxy", "🛡️", [
        "vpn", "proxy", "nordvpn", "hma", "surfshark", "express", "adguard",
        "hotspot", "purevpn", "norton", "proton", "kaspersky"
    ], [
        "nordvpn", "hma_vpn", "surfshark", "express", "adguard_vpn",
        "hotspot_shield", "purevpn", "norton_vpn", "proton", "kaspersky"
    ]),
    ("Wink", "wink", "😉", ["wink"], ["wink"]),
    # Row 15
    ("Xingtu", "xingtu", "📷", ["xingtu"], ["xingtu"]),
    ("Youtube", "youtube", "🔴", ["youtube", "vidiq"], ["youtube"]),
    ("Muse AI", "muse_ai", "🎼", ["muse", "muse ai"], ["muse_ai"]),
    # Row 16
    ("JetBrains", "jetbrains", "💻", ["jetbrains", "intellij", "pycharm"], ["jetbrains"]),
    ("Google One", "google_one", "1️⃣", ["google one", "drive 2tb"], ["google_one"]),
    ("NetFlix", "netflix", "🍿", ["netflix"], ["netflix"]),
    # Row 17
    ("Clico", "clico", "🎯", ["clico", "tryclico"], ["tryclico"]),
    ("Replit", "replit", "🌀", ["replit"], ["replit"]),
    ("Zed", "zed", "⚡", ["zed"], ["zed"]),
    # Row 18
    ("Alight Motion", "alight_motion", "💫", ["alight motion", "alight"], ["alight_motion"]),
    ("Wispr Flow", "wispr_flow", "🌬️", ["wispr flow", "wispr"], ["wispr_flow"]),
    ("Tool Veo3", "tool_veo3", "✦", ["tool veo3", "veo 3", "veo3", "veo"], []),
    # Row 19
    ("Amazon Prime", "amazon_prime", "📦", ["amazon prime", "amazon", "prime video"], ["amazon_prime"]),
    ("linkedin", "linkedin", "💼", ["linkedin"], ["linkedin"]),
    ("GenSpark", "genspark", "✨", ["genspark"], ["genspark"]),
    # Row 20
    ("Framer", "framer", "📐", ["framer"], ["framer"]),
    ("Leonardo AI", "leonardo_ai", "🎨", ["leonardo"], ["leonardo_ai"]),
    ("Pippit AI", "pippit_ai", "🐣", ["pippit", "pipit", "pitpit"], []),
    # Row 21
    ("Claude Official", "claude_official", "✴️", ["claude pro", "claude max", "claude official", "claude 3", "claude x5", "claude"], ["claude"]),
    ("Google Flow Veo3 Ultra", "flow_veo3", "🔺", ["google flow", "veo3 ultra", "admin ultra"], []),
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


def match_product_to_brand(name: str, emoji: Optional[str] = None) -> str:
    """Finds the most specific brand slug for a product."""
    n = name.lower()
    em = (emoji or "").lower()

    # Priority compound brands first
    priority_slugs = ["flow_veo3", "api_claude", "api_codex", "api_deepseek", "api_gemini", "tool_veo3"]
    for slug in priority_slugs:
        meta = BRANDS_DICT[slug]
        if any(kw in n for kw in meta["keywords"]):
            return slug

    # Match by emoji if present
    if em:
        for slug, meta in BRANDS_DICT.items():
            if slug in priority_slugs:
                continue
            if em in meta["emojis"] or any(e in em for e in meta["emojis"]):
                return slug

    # Match by keywords
    for slug, meta in BRANDS_DICT.items():
        if slug in priority_slugs:
            continue
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

    # First check if products have brand_slug populated
    brand_cond = (ProductCache.brand_slug == slug)
    count_by_slug = (await session.execute(count_q.where(brand_cond))).scalar() or 0

    if count_by_slug > 0:
        base_q = base_q.where(brand_cond)
        total_count = count_by_slug
    else:
        cond = get_brand_filter_condition(slug)
        if cond is not None:
            base_q = base_q.where(cond)
            count_q = count_q.where(cond)
        total_count = (await session.execute(count_q)).scalar() or 0
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
