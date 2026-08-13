from urllib.parse import urlparse


class PageAccessError(RuntimeError):
    """Raised when a fetched page cannot be used by the scraper."""


class AuthenticationRequiredError(PageAccessError):
    """Raised when the site redirects the browser to its login page."""


class PageStructureChangedError(PageAccessError):
    """Raised when an authenticated page no longer matches the known layout."""


def ensure_authenticated_page(
    page,
    *,
    expected_site_origin: str,
) -> None:
    resolved_origin = expected_site_origin.rstrip("/")
    current_url = str(page.url)
    if _is_login_page(page, current_url=current_url, expected_site_origin=resolved_origin):
        raise AuthenticationRequiredError(
            "站点登录态已失效，请在“登录与抓取”页面重新登录后再抓取。"
        )

    parsed_url = urlparse(current_url)
    expected_url = urlparse(resolved_origin)
    if (parsed_url.scheme, parsed_url.netloc) != (expected_url.scheme, expected_url.netloc):
        raise PageAccessError("站点页面跳转到了未配置的地址。")


def ensure_page_structure(page, *, required_selector: str, page_name: str) -> None:
    if page.locator(required_selector).count() > 0:
        return

    raise PageStructureChangedError(
        f"{page_name}页面缺少必要元素 {required_selector}。"
        "请检查站点是否改版，或页面是否被拦截。"
        f" current_url={page.url}"
    )


def _is_login_page(page, *, current_url: str, expected_site_origin: str) -> bool:
    parsed_url = urlparse(current_url)
    expected_url = urlparse(expected_site_origin)
    if parsed_url.netloc != expected_url.netloc:
        return False

    if parsed_url.path.rstrip("/") == "/login":
        return True
    return page.locator("#loginform").count() > 0