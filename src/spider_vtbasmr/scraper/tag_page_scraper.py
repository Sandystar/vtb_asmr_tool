from dataclasses import asdict, dataclass

from spider_vtbasmr.browser.playwright_browser_client import BrowserSession, PlaywrightBrowserClient
from spider_vtbasmr.manager.config_manager import ConfigManager
from spider_vtbasmr.scraper.page_access import ensure_authenticated_page, ensure_page_structure


@dataclass(slots=True)
class CoverItem:
    post_id: str
    title: str
    detail_url: str
    cover_image_url: str
    excerpt: str
    published_at: str
    price_label: str
    tags: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class PaginationItem:
    page_number: int
    page_url: str
    is_active: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TagPageResult:
    page_url: str
    tag_name: str
    cover_items: list[CoverItem]
    pagination_items: list[PaginationItem]

    def to_dict(self) -> dict[str, object]:
        return {
            "page_url": self.page_url,
            "tag_name": self.tag_name,
            "cover_items": [cover_item.to_dict() for cover_item in self.cover_items],
            "pagination_items": [pagination_item.to_dict() for pagination_item in self.pagination_items],
        }


class TagPageScraper:
    def __init__(
        self,
        browser_client: PlaywrightBrowserClient | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigManager()
        self._browser_client = browser_client or PlaywrightBrowserClient(
            config_manager=self._config_manager,
        )
        self._login_state = self._config_manager.get_storage_state()
        self._site_origin = self._config_manager.get_site_origin()

    def scrape_tag_page(
        self,
        page_url: str,
        *,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
        browser_session: BrowserSession | None = None,
    ) -> TagPageResult:
        if browser_session is None:
            managed_browser_session = self._browser_client.open_logged_in_browser_session(
                storage_state=self._login_state or {},
                is_headless=is_headless,
            )
        else:
            managed_browser_session = browser_session

        try:
            page = managed_browser_session.page
            page.goto(page_url, wait_until="networkidle", timeout=timeout_milliseconds)
            ensure_authenticated_page(page, expected_site_origin=self._site_origin)
            ensure_page_structure(
                page,
                required_selector=".archive-title",
                page_name="Tag归档",
            )

            tag_name = page.locator(".archive-title").inner_text().strip()
            cover_items = self._extract_cover_items(page)
            pagination_items = self._extract_pagination_items(page, current_page_url=page.url)
            final_url = page.url
        finally:
            if browser_session is None:
                self._browser_client.close_browser_session(managed_browser_session)

        return TagPageResult(
            page_url=final_url,
            tag_name=tag_name,
            cover_items=cover_items,
            pagination_items=pagination_items,
        )

    def _extract_cover_items(self, page) -> list[CoverItem]:
        cover_items: list[CoverItem] = []
        post_locator = page.locator("#posts .post.grid")
        post_count = post_locator.count()

        for index in range(post_count):
            current_post = post_locator.nth(index)
            post_id = current_post.get_attribute("data-id") or ""
            title_anchor = current_post.locator("h3 a")
            cover_image = current_post.locator(".img img")
            tag_links = current_post.locator(".tag a")
            tag_count = tag_links.count()
            tags = [tag_links.nth(tag_index).inner_text().strip() for tag_index in range(tag_count)]

            price_locator = current_post.locator(".grid-meta .price")
            published_at_locator = current_post.locator(".grid-meta .time")
            excerpt_locator = current_post.locator(".excerpt")

            published_at = published_at_locator.inner_text().replace("\n", " ").strip() if published_at_locator.count() > 0 else ""
            price_label = price_locator.inner_text().replace("\n", " ").strip() if price_locator.count() > 0 else ""
            excerpt = excerpt_locator.inner_text().strip() if excerpt_locator.count() > 0 else ""

            cover_items.append(
                CoverItem(
                    post_id=post_id,
                    title=title_anchor.inner_text().strip(),
                    detail_url=title_anchor.get_attribute("href") or "",
                    cover_image_url=cover_image.get_attribute("src") or "",
                    excerpt=excerpt,
                    published_at=published_at,
                    price_label=price_label,
                    tags=tags,
                )
            )

        return cover_items

    def _extract_pagination_items(self, page, current_page_url: str) -> list[PaginationItem]:
        discovered_page_numbers = self._extract_discovered_page_numbers(page)
        max_page_number = max(discovered_page_numbers, default=1)
        page_url_prefix = self._build_page_url_prefix(page, current_page_url=current_page_url)
        current_page_number = self._extract_current_page_number(page, current_page_url=current_page_url)

        return [
            PaginationItem(
                page_number=page_number,
                page_url=self._build_page_url(page_url_prefix=page_url_prefix, page_number=page_number),
                is_active=page_number == current_page_number,
            )
            for page_number in range(1, max_page_number + 1)
        ]

    def _extract_discovered_page_numbers(self, page) -> list[int]:
        discovered_page_numbers: set[int] = set()
        pagination_link_locator = page.locator(".pagination li")
        pagination_count = pagination_link_locator.count()

        for index in range(pagination_count):
            pagination_item_locator = pagination_link_locator.nth(index)
            label = pagination_item_locator.inner_text().replace("\n", " ").strip()
            if label.isdigit():
                discovered_page_numbers.add(int(label))
                continue

            anchor_locator = pagination_item_locator.locator("a")
            if anchor_locator.count() == 0:
                continue

            page_url = anchor_locator.get_attribute("href") or ""
            page_number = self._extract_page_number_from_url(page_url)
            if page_number is not None:
                discovered_page_numbers.add(page_number)

        return sorted(discovered_page_numbers)

    def _extract_current_page_number(self, page, current_page_url: str) -> int:
        active_locator = page.locator(".pagination li.active")
        if active_locator.count() > 0:
            active_text = active_locator.first.inner_text().strip()
            if active_text.isdigit():
                return int(active_text)

        current_page_number = self._extract_page_number_from_url(current_page_url)
        return current_page_number or 1

    def _build_page_url_prefix(self, page, current_page_url: str) -> str:
        pagination_link_locator = page.locator(".pagination li a")
        pagination_link_count = pagination_link_locator.count()

        for index in range(pagination_link_count):
            page_url = pagination_link_locator.nth(index).get_attribute("href") or ""
            page_number = self._extract_page_number_from_url(page_url)
            if page_number is not None:
                return page_url.rsplit(f"/page/{page_number}", 1)[0]

        current_page_number = self._extract_page_number_from_url(current_page_url)
        if current_page_number is not None:
            return current_page_url.rsplit(f"/page/{current_page_number}", 1)[0]

        return current_page_url.rstrip("/")

    def _build_page_url(self, page_url_prefix: str, page_number: int) -> str:
        normalized_prefix = page_url_prefix.rstrip("/")
        if page_number == 1:
            return normalized_prefix
        return f"{normalized_prefix}/page/{page_number}"

    def _extract_page_number_from_url(self, page_url: str) -> int | None:
        marker = "/page/"
        if marker not in page_url:
            return None

        page_number_text = page_url.rsplit(marker, 1)[-1].strip("/")
        if page_number_text.isdigit():
            return int(page_number_text)
        return None
