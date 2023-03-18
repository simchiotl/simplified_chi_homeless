import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, CookieManager
from schomeless.schema import Chapter, Book, BookInfoRequest, CatalogueRequest, ChapterRequest
from schomeless.utils import RequestsTool

__all__ = [
    'LongmaApi'
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'LONGMA'


@CookieManager.register(namespace.lower())
def add_longma_cookies(cookie=None):
    """

    Args:
        cookie (str, optional): cookie string like ``"key=name;key2=name2"``. If provided, use it. \
                                Otherwise, get new cookie by re-login.
    """

    def token_exist(browser):
        cookies = browser.get_cookies()
        return any(a['name'] == 'token' for a in cookies)

    info = CookieManager.load_info(namespace.lower())
    if cookie is None:
        browser = webdriver.Chrome()
        browser.get('https://members.longma.tw/apps/login.php')
        browser.find_element(value='jj_login').click()
        browser.find_element(value='loginname').send_keys(info.get('name', ''))
        browser.find_element(value='loginpassword').send_keys(info.get('password', ''))
        browser.find_element(value='login_registerRule').click()
        browser.find_element(value='login_cookietime').click()
        WebDriverWait(browser, timeout=300).until(token_exist)
        cookie = ';'.join(f"{a['name']}={a['value']}" for a in browser.get_cookies())
        browser.quit()
        logger.info('Login succeeded.')
    return cookie


@RequestApi.register(namespace)
class LongmaApi(RequestApi):
    CATALOGUE_API = "https://ebook.longmabook.com/showbooklist.php"
    CONTENT_API = "https://ebook.longmabook.com/showpapercolor.php"
    CHAPTER_API = "https://ebook.longmabook.com/?act=showpaper&paperid={req.chapter_id}"
    WEB_ENCODING = 'utf-8'
    CONTENT_ENCODING = 'UTF-8-SIG'

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        book_id: int

    @dataclass
    class ChapterRequest(ChapterRequest):
        chapter_id: int
        title: Optional[str] = None

    def __init__(self):
        super().__init__()
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            'cookie': self.cookies
        }

    @staticmethod
    def _parse_last_id(url):
        return int(url.strip('/').split('/')[-1])

    # ====================== Get Chapter ===========================
    def _parse_hash(self, req, page):
        if len(page('#paperbuybtm')) > 0:
            return None
        parts = page.html().split("vercodechk: '", maxsplit=1)
        if len(parts) > 1:
            return parts[1].split("'", maxsplit=1)[0]
        return ''

    def _postprocess_chapter(self, req, page, d):
        title = page('h3.uk-card-title').text().strip().split('\n')[-1]
        content = d.text().strip()
        hrefs = list(
            item.attrib['href'] for item in page('#bottomNav a') if item.attrib.get('uk-icon', None) == 'chevron-right')
        next = None
        if len(hrefs) > 0:
            next = LongmaApi._url_to_chapter_req("http://a.com" + hrefs[0])
        return Chapter(title, content), next

    @staticmethod
    def _url_to_chapter_req(url):
        query = RequestsTool.parse_query(url)
        chapter_id = None
        if 'paperid' in query:
            chapter_id = int(query['paperid'])
        return LongmaApi.ChapterRequest(True, chapter_id)

    def _page_request_payload(self, req):
        headers = dict(**self.headers)
        chap_link = LongmaApi.CHAPTER_API.format(req=req)
        return dict(
            url=chap_link,
            encoding=LongmaApi.WEB_ENCODING,
            request_kwargs=dict(headers=headers)
        )

    def _content_request_payload(self, req, payload, page):
        hash = self._parse_hash(req, page)
        if hash is None:
            return None
        payload['request_kwargs']['headers'].update({
            'referer': payload['url'],
        })
        params = {
            'paperid': req.chapter_id,
            'vercodechk': hash
        }
        payload['url'] = LongmaApi.CONTENT_API
        payload['encoding'] = LongmaApi.CONTENT_ENCODING
        payload['method'] = 'POST'
        payload['request_kwargs']['data'] = params
        return payload

    def get_chapter(self, req):
        if not isinstance(req, LongmaApi.ChapterRequest):
            req = LongmaApi._url_to_chapter_req(req.url)
        payload = self._page_request_payload(req)
        page = RequestsTool.request_and_pyquery(**payload)
        payload = self._content_request_payload(req, payload, page)
        if payload is not None:
            d = RequestsTool.request_and_pyquery(**payload)
            return self._postprocess_chapter(req, page, d)
        return Chapter(req.title, ''), None

    async def get_chapter_async(self, session, req):
        if not isinstance(req, LongmaApi.ChapterRequest):
            req = LongmaApi._url_to_chapter_req(req.url)
        payload = self._page_request_payload(req)
        page = await RequestsTool.request_and_pyquery_async(session, **payload)
        payload = self._content_request_payload(req, payload, page)
        if payload is not None:
            d = await RequestsTool.request_and_pyquery_async(session, **payload)
            return self._postprocess_chapter(req, page, d)
        return Chapter(req.title, ''), None

    # ====================== Get Chapter List ===========================
    def get_chapter_list(self, req):
        """Get the chapter links

        Args:
            req (CatalogueRequest):

        Returns:
            list[ChapterRequest]
        """
        chapters = []
        pid = 1
        host = RequestsTool.get_host(LongmaApi.CATALOGUE_API)
        while True:
            params = {
                'ebookid': req.book_id,
                'pages': pid,
                'showbooklisttype': 0
            }
            d = RequestsTool.request_and_pyquery(
                LongmaApi.CATALOGUE_API,
                LongmaApi.CONTENT_ENCODING,
                request_kwargs=dict(headers=self.headers, data=params),
                method='POST'
            )
            items = d('a')
            n = len(items)
            new_chapters = []
            for i in range(n):
                item = items.eq(i)
                href = item.attr('href')
                if not href or 'showpaper' not in href: continue
                creq = LongmaApi._url_to_chapter_req(host + href)
                creq.title = item.text().strip()
                new_chapters.append(creq)
            pid += 1
            has_next = len(new_chapters) > 0 and (not chapters or new_chapters[-1] != chapters[-1])
            if not has_next:
                break
            chapters += new_chapters
        return chapters

    # ====================== Get Book Info ==============================
    def get_book_info(self, req):
        params = {
            'ebookid': req.book_id,
            'showbooklisttype': 0
        }
        d = RequestsTool.request_and_pyquery(
            LongmaApi.CATALOGUE_API,
            LongmaApi.CONTENT_ENCODING,
            request_kwargs=dict(headers=self.headers, data=params),
            method='POST'
        )
        items = d('li')
        n = len(items)
        for i in range(n):
            item = items.eq(i)
            text = item.text().strip()
            title = f"【作品編號：{req.book_id}】"
            if title in text:
                return Book(preface=text)
        return Book()

    # ====================== Buy chapter ==============================
    def buy_chapters(self, requests, retry_count=None):
        """

        Args:
            requests (list[LongmaApi.ChapterRequest]):
        """

        def fine_button(browser):
            try:
                return browser.find_element(value='paperbuybtm')
            except NoSuchElementException as e:
                return None

        cookies = CookieManager.parse_cookie(self.cookies)
        host = RequestsTool.get_host(LongmaApi.CHAPTER_API)
        browser = webdriver.Chrome()
        browser.get(host)
        for k, v in cookies.items():
            browser.add_cookie({"name": k, "value": v})
        for req in requests:
            browser.get(LongmaApi.CHAPTER_API.format(req=req))
            e = fine_button(browser)
            if e is not None:
                retry = 0
                while retry_count is None or retry < retry_count:
                    try:
                        e.click()
                        break
                    except ElementClickInterceptedException:
                        e.send_keys(Keys.DOWN)
                        retry += 1
