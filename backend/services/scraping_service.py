from typing import Optional, Dict, Any, List
import io, re, os, contextlib, urllib.parse

from services.facebook_scraping import get_facebook_stats as fb_get_stats
from services.google_scraping import get_google_maps_rating as gm_get_rating
from services.tiktok_scraping import TikTokScraper


# -------------------- URL helpers --------------------

def _last_path_segment(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
        seg = [s for s in path.split("/") if s][-1] if path else url
        return urllib.parse.unquote(seg)
    except Exception:
        return url

def _facebook_username_from_url(url_or_user: str) -> str:
    if url_or_user.startswith("http"):
        seg = _last_path_segment(url_or_user)
        # casitos típicos: /people/Nombre/12345 -> tomar el penúltimo si es 'people'
        if "/people/" in url_or_user:
            parts = [s for s in urllib.parse.urlparse(url_or_user).path.split("/") if s]
            if len(parts) >= 3:
                return parts[-2]
        return seg
    return url_or_user

def _tiktok_username_from_url(url_or_user: str) -> str:
    if url_or_user.startswith("http"):
        seg = _last_path_segment(url_or_user)  # suele ser '@usuario'
        return seg.lstrip("@")
    return url_or_user.lstrip("@")

def _guess_business_from_url(url: str) -> Optional[str]:
    """
    Heurística para Google Maps si nos pasan una URL y NO tenemos API de place_id:
    - toma el último segmento legible (sin @coords/@data)
    """
    try:
        seg = _last_path_segment(url)
        # si viene algo tipo 'data=!3m1!4b1' ignorar
        if seg.startswith("data=") or seg == "":
            return None
        # reemplazos básicos
        seg = seg.replace("-", " ").replace("_", " ").strip()
        return seg if seg else None
    except Exception:
        return None

# -------------------- Parsers utilitarios --------------------

def _find_int(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    s = m.group(1).replace(".", "").replace(",", "")
    return int(s) if s.isdigit() else None

def _log_scale_5(n: int) -> float:
    import math
    if not n or n <= 0:
        return 0.0
    return round(min(5.0, max(0.0, (math.log10(n) + 1.0))), 2)

# -------------------- Wrappers a tus scrapers --------------------

def fetch_google_maps_existing(
    business_name: Optional[str] = None,
    location: Optional[str] = None,              # se ignora para evitar 'll'
    google_maps_url: Optional[str] = None,
    country: Optional[str] = None                # <-- nuevo
) -> Dict[str, Any]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {"platform": "google_maps", "ok": False, "error": "SERPAPI_API_KEY missing"}
    
    parts = []
    if google_maps_url:
        hint = _guess_business_from_url(google_maps_url)
        if hint: parts.append(hint)
    if business_name:
        parts.append(business_name)
    if country:
        parts.append(country)

    seen = set()
    query = " ".join([p for p in parts if not (p in seen or seen.add(p))]).strip()

    if not query:
        return {"platform": "google_maps", "ok": False, "error": "no query"}

    try:
        rating, reviews, comments = gm_get_rating(api_key, query, "")
        return {
            "platform": "google_maps",
            "ok": rating is not None,
            "rating": rating,
            "reviews": reviews,
            "comments": comments,
            "query_used": query
        }
    except Exception as e:
        return {"platform": "google_maps", "ok": False, "error": str(e), "query_used": query}

def fetch_facebook_existing(username_or_url: str) -> Dict[str, Any]:
    """
    Tu función imprime a stdout. Capturamos y parseamos.
    Acepta username o URL completa.
    """
    try:
        username = _facebook_username_from_url(username_or_url)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fb_get_stats(username)
        out = buf.getvalue()

        followers = _find_int(out, r"Followers count for .*?:\s*([\d\.]+)")
        likes     = _find_int(out, r"Liked count for .*?:\s*([\d\.]+)")
        posts     = _find_int(out, r"Total posts for .*?:\s*([\d\.]+)")

        ok = any([followers, likes, posts])
        return {"platform": "facebook", "ok": ok, "followers": followers, "likes": likes, "posts": posts, "username_used": username}
    except Exception as e:
        return {"platform": "facebook", "ok": False, "error": str(e)}

def fetch_tiktok_existing(username_or_url: str, headless: bool = True) -> Dict[str, Any]:
    try:
        username = _tiktok_username_from_url(username_or_url)
        scraper = TikTokScraper(use_selenium=True, headless=headless)
        try:
            import threading
            result = {}
            def _run():
                nonlocal result
                result = scraper.get_tiktok_stats(username) or {}
            t = threading.Thread(target=_run, daemon=True)
            t.start(); t.join(15)  # 15s máx
            stats = result if not t.is_alive() else {}
        finally:
            scraper.close()
        if not stats:
            return {"platform": "tiktok", "ok": False, "error": "timeout/no stats", "username_used": username}
        out = {"platform": "tiktok", "ok": bool(stats.get("found", False))}
        for k in ("followers", "likes", "bio", "url"):
            if k in stats: out[k] = stats[k]
        out["username_used"] = username
        return out
    except Exception as e:
        return {"platform": "tiktok", "ok": False, "error": str(e)}


# -------------------- Facade principal --------------------

def collect_public_signals_existing(
    business_name: Optional[str],
    city: Optional[str],
    instagram: Optional[str],
    facebook: Optional[str],
    tiktok: Optional[str],
    google_maps_url: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orquesta: usa URL si viene; si no, cae al modo por nombre.
    Calcula digital_rating 0..5 con pesos.
    """
    platforms: Dict[str, Any] = {}

    # Google Maps: URL primero, si no -> nombre
    if business_name or google_maps_url:
        platforms["google_maps"] = fetch_google_maps_existing(
            business_name=business_name,
            location=None,                   # ← ignorado a propósito
            google_maps_url=google_maps_url,
            country=country                  # ← aquí
        )

    if facebook:
        platforms["facebook"] = fetch_facebook_existing(facebook)

    if tiktok:
        platforms["tiktok"] = fetch_tiktok_existing(tiktok, headless=True)

    scores: List[float] = []
    weights: List[float] = []

    gm = platforms.get("google_maps")
    if gm and gm.get("ok") and gm.get("rating") is not None:
        scores.append(float(gm["rating"])); weights.append(3.0)

    fb = platforms.get("facebook")
    if fb and fb.get("ok") and fb.get("followers"):
        scores.append(_log_scale_5(fb["followers"])); weights.append(1.0)

    tk = platforms.get("tiktok")
    if tk and tk.get("ok") and tk.get("followers"):
        scores.append(_log_scale_5(tk["followers"])); weights.append(1.0)

    if scores:
        total_w = sum(weights)
        digital_rating = round(sum(s*w for s, w in zip(scores, weights)) / total_w, 2)
    else:
        digital_rating = None

    return {"platforms": platforms, "digital_rating": digital_rating}
