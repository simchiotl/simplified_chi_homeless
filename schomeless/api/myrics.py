import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from pyquery import PyQuery
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest, BookInfoRequest
from schomeless.utils import RequestsTool

__all__ = [
    'MyRicsApi',
    'add_myrics_cookies',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'MY-RICS'


@CookieManager.register(namespace.lower())
def add_myrics_cookies(cookie=None):
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
        browser.get('https://www.jjwxc.net/')
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
class MyRicsApi(RequestApi):
    BOOK_API = "https://www.my-rics.club/novels/{req.book_id}"
    BOOK_INFO_API = "https://www.my-rics.club/authors/api_novel_detailed/{req.book_id}"
    CATALOGUE_API = "https://www.my-rics.club/novels/menu"
    CHAPTER_WEB_API = "https://www.my-rics.club/chapters/{req.chapter_id}"
    WEB_ENCODING = 'utf-8'
    API_ENCODING = 'ascii'

    @dataclass
    class ChapterRequest(ChapterRequest):
        chapter_id: int
        title: Optional[str] = None

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        book_id: int

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    def __init__(self):
        super().__init__()
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            'cookie': self.cookies + '; django_language=zh-hans',
        }

    @staticmethod
    def _get_title(title):
        return title.split('章', maxsplit=1)[-1].strip()

    @staticmethod
    def _parse_request_from_chapter_url(url):
        try:
            return MyRicsApi.ChapterRequest(True, int(url.split('/')[-1]))
        except Exception as e:
            raise ValueError(f'Invalid MY-RICS chapter URL: `{url}`')

    @staticmethod
    def _parse_chapter(req, text):
        d = PyQuery(text)
        title = d('h1').text().split('.', maxsplit=1)[-1].strip()
        title = MyRicsApi._get_title(title)
        content = d('div.wysiwyg:first').text()
        next = None
        arrow = [f for f in text.split('@click.prevent="') if f.startswith('check') and '下一章' in f]
        if len(arrow) > 0:
            cid = int(arrow[-1].split(')', maxsplit=1)[0].split('(', maxsplit=1)[-1])
            next = MyRicsApi.ChapterRequest(True, cid)
        return Chapter(title, content), next

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or MyRicsApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, MyRicsApi.ChapterRequest=None)``. If ``MyRicsApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = MyRicsApi._parse_request_from_chapter_url(req.url)
        text = RequestsTool.request(
            MyRicsApi.CHAPTER_WEB_API.format(req=req),
            encoding=MyRicsApi.WEB_ENCODING,
            request_kwargs=dict(headers=self.headers)
        )
        return MyRicsApi._parse_chapter(req, text)

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or MyRicsApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, MyRicsApi.ChapterRequest=None)``. If ``MyRicsApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = MyRicsApi._parse_request_from_chapter_url(req.url)
        text = await RequestsTool.request_async(
            session,
            MyRicsApi.CHAPTER_WEB_API.format(req=req),
            encoding=MyRicsApi.WEB_ENCODING,
            request_kwargs=dict(headers=self.headers)
        )
        return MyRicsApi._parse_chapter(req, text)

    # ====================== Get chapter list ===========================
    @staticmethod
    def _catalogue_url_to_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            MyRicsApi.CatalogueRequest
        """
        try:
            return MyRicsApi.CatalogueRequest(book_id=int(req.url.split('/')[-1]))
        except Exception as e:
            raise ValueError(f'Invalid MY-RICS catalogue URL: `{req.url}`')

    def get_chapter_list_web(self, req):
        pid = 1
        total = None
        res = []
        while True:
            params = {
                "id": req.book_id,
                'page': pid,
                'sort': 'asc'
            }
            d = RequestsTool.request_and_json(
                MyRicsApi.CATALOGUE_API,
                MyRicsApi.API_ENCODING,
                request_kwargs=dict(headers=self.headers, json=params),
                method='POST'
            )
            if total is None:
                total = d['data']['total_page']
            items = d['data']['list']
            res += [MyRicsApi.ChapterRequest(True, int(item['id']), MyRicsApi._get_title(item['title']))
                    for item in items]
            if pid == total:
                break
            pid += 1
        return res

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or MyRicsApi.CatalogueRequest):

        Returns:
            list[MyRicsApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = MyRicsApi._catalogue_url_to_request(req)
        chapters = self.get_chapter_list_web(req)
        return chapters
