"""MarkdownifyNode — convert fetched HTML into clean text for the LLM."""

import re

from bs4 import BeautifulSoup, Comment

from ..config import MAX_CONTENT_CHARS, PER_PAGE_CHARS
from ..graph.base_node import BaseNode

STRIP = ["script", "style", "noscript", "svg", "img", "video", "audio", "iframe", "canvas"]


class MarkdownifyNode(BaseNode):
    def execute(self, state: dict) -> dict:
        sections = []
        total_chars = 0
        for page in state["pages"]:
            text = self._clean(page["html"])
            page["markdown"] = text
            total_chars += len(text)
            # Per-page cap so a bloated homepage can't starve contact/about pages
            sections.append(f"=== {page['page_type'].upper()}: {page['url']} ===\n{text[:PER_PAGE_CHARS]}")
        state["combined_markdown"] = "\n\n".join(sections)[:MAX_CONTENT_CHARS]
        state["content_chars"] = total_chars
        return state

    @staticmethod
    def _clean(html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(STRIP):
            tag.decompose()
        for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
            c.extract()
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r"\n{3,}", "\n\n", text)
