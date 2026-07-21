from dataclasses import asdict, dataclass
import re

from spider_vtbasmr.browser.playwright_browser_client import BrowserSession, PlaywrightBrowserClient
from spider_vtbasmr.manager.config_manager import ConfigManager


@dataclass(slots=True)
class DownloadLinkItem:
    link_type: str
    link_url: str
    link_text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class DetailPageResult:
    page_url: str
    title: str
    published_at: str
    excerpt: str
    tags: list[str]
    access_status: str
    access_message: str
    hidden_content_html: str
    hidden_content_text: str
    download_links: list[DownloadLinkItem]
    extraction_code: str
    archive_password: str

    def to_dict(self) -> dict[str, object]:
        return {
            "page_url": self.page_url,
            "title": self.title,
            "published_at": self.published_at,
            "excerpt": self.excerpt,
            "tags": self.tags,
            "access_status": self.access_status,
            "access_message": self.access_message,
            "hidden_content_html": self.hidden_content_html,
            "hidden_content_text": self.hidden_content_text,
            "download_links": [download_link.to_dict() for download_link in self.download_links],
            "extraction_code": self.extraction_code,
            "archive_password": self.archive_password,
        }


class DetailPageScraper:
    def __init__(
        self,
        browser_client: PlaywrightBrowserClient | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self._config_manager = config_manager or ConfigManager()
        self._browser_client = browser_client or PlaywrightBrowserClient(
            config_manager=self._config_manager,
        )
        self._login_state_path = self._config_manager.get_login_state_file_path()
        self._download_link_info = self._config_manager.get_download_link_info()

    def scrape_detail_page(
        self,
        page_url: str,
        *,
        is_headless: bool = True,
        timeout_milliseconds: int = 60000,
        browser_session: BrowserSession | None = None,
    ) -> DetailPageResult:
        if browser_session is None:
            managed_browser_session = self._browser_client.open_logged_in_browser_session(
                storage_state_path=self._login_state_path,
                is_headless=is_headless,
            )
        else:
            managed_browser_session = browser_session

        try:
            page = managed_browser_session.page
            page.goto(page_url, wait_until="networkidle", timeout=timeout_milliseconds)
            self._dismiss_site_tips_popup(page)

            title = self._get_text(page, ".article-title")
            published_at = self._extract_published_at(page)
            excerpt = self._extract_excerpt(page)
            tags = self._extract_tags(page)

            access_status, access_message, hidden_content_html, hidden_content_text = self._reveal_hidden_content(
                page=page,
                timeout_milliseconds=timeout_milliseconds,
            )
            download_links = self._extract_download_links(page, hidden_content_text=hidden_content_text)
            extraction_code = self._extract_labeled_value(hidden_content_text, label_prefix="提取码：")
            archive_password = self._extract_labeled_value(hidden_content_text, label_prefix="解压密码：")
            final_url = page.url
        finally:
            if browser_session is None:
                self._browser_client.close_browser_session(managed_browser_session)

        return DetailPageResult(
            page_url=final_url,
            title=title,
            published_at=published_at,
            excerpt=excerpt,
            tags=tags,
            access_status=access_status,
            access_message=access_message,
            hidden_content_html=hidden_content_html,
            hidden_content_text=hidden_content_text,
            download_links=download_links,
            extraction_code=extraction_code,
            archive_password=archive_password,
        )

    def _dismiss_site_tips_popup(self, page) -> None:
        shadow_locator = page.locator(".sitetips-pop-shadow")
        if shadow_locator.count() > 0:
            try:
                shadow_locator.first.click(force=True)
                page.wait_for_timeout(500)
            except Exception:
                pass

        close_locator = page.locator(".sitetips-pop .close")
        if close_locator.count() > 0:
            try:
                close_locator.first.click(force=True)
                page.wait_for_timeout(500)
            except Exception:
                pass

    def _reveal_hidden_content(self, page, timeout_milliseconds: int) -> tuple[str, str, str, str]:
        hidden_content_locator = page.locator(".erphpdown-content-view")
        if hidden_content_locator.count() > 0:
            hidden_content_html = hidden_content_locator.first.inner_html()
            hidden_content_text = hidden_content_locator.first.inner_text().strip()
            return "available", "Hidden content already visible.", hidden_content_html, hidden_content_text

        see_button_locator = page.locator(".erphpdown-see-btn")
        if see_button_locator.count() == 0:
            return "not_required", "No hidden content gate was detected.", "", ""

        try:
            see_button_locator.first.click(force=True, timeout=timeout_milliseconds)
            page.wait_for_timeout(3000)
        except Exception as error:
            access_message = self._extract_access_message(page)
            return "interaction_failed", f"Failed to click see button. {access_message or error}", "", ""

        hidden_content_locator = page.locator(".erphpdown-content-view")
        if hidden_content_locator.count() > 0:
            hidden_content_html = hidden_content_locator.first.inner_html()
            hidden_content_text = hidden_content_locator.first.inner_text().strip()
            return "available", "Hidden content revealed successfully.", hidden_content_html, hidden_content_text

        access_message = self._extract_access_message(page)
        access_status = self._classify_access_status(access_message)
        return access_status, access_message, "", ""

    def _extract_access_message(self, page) -> str:
        candidate_selectors = [
            ".erphpdown-content-vip-see",
            ".erphpdown-box",
            ".swal2-container",
            ".layui-layer",
            ".site-message",
            ".article-content",
        ]
        for selector in candidate_selectors:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            text = locator.first.inner_text().strip()
            if any(keyword in text for keyword in ["查看", "会员", "权限", "次数", "VIP", "积分"]):
                return text
        return "Hidden content is still unavailable after interaction."

    def _classify_access_status(self, access_message: str) -> str:
        if "次数" in access_message or "还可查看0个" in access_message:
            return "daily_limit_reached"
        if "会员" in access_message or "VIP" in access_message or "权限" in access_message:
            return "membership_required"
        return "unavailable"

    def _extract_download_links(self, page, *, hidden_content_text: str) -> list[DownloadLinkItem]:
        download_links: list[DownloadLinkItem] = []
        matched_link_urls: set[str] = set()
        content_locator = page.locator(".erphpdown-content-view a")
        content_link_count = content_locator.count()

        for index in range(content_link_count):
            link_locator = content_locator.nth(index)
            link_url = link_locator.get_attribute("href") or ""
            link_text = link_locator.inner_text().strip()
            link_type = self._match_download_link_type(link_url)
            if link_url and link_type and link_url not in matched_link_urls:
                matched_link_urls.add(link_url)
                download_links.append(
                    DownloadLinkItem(
                        link_type=link_type,
                        link_url=link_url,
                        link_text=link_text or link_url,
                    )
                )

        if download_links:
            return download_links

        return self.extract_download_links_from_text(hidden_content_text)

    def extract_download_links_from_text(self, hidden_content_text: str) -> list[DownloadLinkItem]:
        if not hidden_content_text.strip():
            return []

        download_links: list[DownloadLinkItem] = []
        matched_link_urls: set[str] = set()
        link_url_candidates = re.findall(r"https?://[^\s\"'<>]+", hidden_content_text)

        for link_url_candidate in link_url_candidates:
            normalized_link_url = link_url_candidate.rstrip(".,;)")
            link_type = self._match_download_link_type(normalized_link_url)
            if not link_type:
                continue
            if normalized_link_url in matched_link_urls:
                continue
            matched_link_urls.add(normalized_link_url)
            download_links.append(
                DownloadLinkItem(
                    link_type=link_type,
                    link_url=normalized_link_url,
                    link_text=normalized_link_url,
                )
            )

        return download_links

    def _match_download_link_type(self, link_url: str) -> str:
        for link_type, link_prefix in self._download_link_info.items():
            if link_url.startswith(link_prefix):
                return link_type
        return ""

    def _extract_labeled_value(self, text: str, label_prefix: str) -> str:
        for line in text.splitlines():
            normalized_line = line.strip()
            if normalized_line.startswith(label_prefix):
                return normalized_line.removeprefix(label_prefix).strip()
        return ""

    def _extract_excerpt(self, page) -> str:
        article_content_locator = page.locator(".article-content > p")
        paragraph_count = article_content_locator.count()
        for index in range(paragraph_count):
            text = article_content_locator.nth(index).inner_text().strip()
            if text and "百度网盘下载" not in text:
                return text
        return ""

    def _extract_published_at(self, page) -> str:
        candidate_selectors = [
            ".article-meta .item time",
            ".article-meta time",
            ".article-meta .meta-time",
            ".article-meta .item",
            ".article-meta",
        ]
        for selector in candidate_selectors:
            locator = page.locator(selector)
            locator_count = locator.count()
            for index in range(locator_count):
                published_at_candidate = locator.nth(index).inner_text().replace("\n", " ").strip()
                normalized_published_at = self._normalize_published_at(published_at_candidate)
                if normalized_published_at:
                    return normalized_published_at
        return ""

    def _normalize_published_at(self, published_at: str) -> str:
        normalized_text = published_at.strip()
        if not normalized_text:
            return ""
        normalized_text = normalized_text.replace("年", "-").replace("月", "-").replace("日", "")
        date_match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", normalized_text)
        if date_match is None:
            return ""
        year_text, month_text, day_text = date_match.groups()
        return f"{year_text}-{int(month_text):02d}-{int(day_text):02d}"

    def _extract_tags(self, page) -> list[str]:
        tag_locator = page.locator(".article-tags a")
        tag_count = tag_locator.count()
        return [tag_locator.nth(index).inner_text().strip() for index in range(tag_count)]

    def _get_text(self, page, selector: str) -> str:
        locator = page.locator(selector)
        if locator.count() == 0:
            return ""
        return locator.first.inner_text().replace("\n", " ").strip()
