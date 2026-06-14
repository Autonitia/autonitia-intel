"""FetchNode — fetch the target URL plus a few relevant sub-pages."""

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..config import MAX_SUBPAGES
from ..fetchers import fetch_html
from ..graph.base_node import BaseNode

# Lower number = higher priority. Contact/about pages hold the lead-relevant
# details (addresses, WhatsApp, emails), so they're fetched before service pages.
SUBPAGE_PRIORITY = {
    "contact": 1, "about": 2, "pricing": 3, "book": 4, "appointment": 4, "services": 5,
}


class FetchNode(BaseNode):
    def execute(self, state: dict) -> dict:
        url = state["target_url"]
        use_cache = state.get("use_cache", True)

        main_html = fetch_html(url, use_cache=use_cache)
        pages = [{"url": url, "html": main_html, "page_type": "homepage"}]

        # Light sub-page discovery for better capability/pricing detection
        for sp in self._discover(main_html, url)[:MAX_SUBPAGES]:
            try:
                pages.append({"url": sp, "html": fetch_html(sp, use_cache=use_cache),
                              "page_type": self._page_type(sp)})
            except Exception:
                pass

        state["pages"] = pages
        state["combined_html"] = "\n".join(p["html"] for p in pages)
        return state

    @staticmethod
    def _discover(html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        domain = urlparse(base_url).netloc
        # url -> best (lowest) priority seen, keeping one URL per page_type for variety
        candidates: dict[str, int] = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.get_text(strip=True).lower()
            for kw, prio in SUBPAGE_PRIORITY.items():
                if kw in href or kw in text:
                    full = urljoin(base_url, a["href"])
                    if urlparse(full).netloc == domain:
                        candidates[full] = min(candidates.get(full, 99), prio)
                    break
        # Sort by priority, then dedupe by page_type so we don't fetch 3 service pages
        ranked = sorted(candidates.items(), key=lambda kv: kv[1])
        out, seen_types = [], set()
        for url, _ in ranked:
            ptype = FetchNode._page_type(url)
            if ptype in seen_types:
                continue
            seen_types.add(ptype)
            out.append(url)
        return out

    @staticmethod
    def _page_type(url: str) -> str:
        low = url.lower()
        for k in ("contact", "pricing", "book", "about", "services"):
            if k in low:
                return k
        return "other"
