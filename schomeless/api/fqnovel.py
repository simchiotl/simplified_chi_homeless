import json
import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from pyquery import PyQuery
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager, UrlBookInfoRequest
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest, BookInfoRequest, Book
from schomeless.utils import RequestsTool

__all__ = [
    'FqNovelApi',
    'add_fqnovel_cookies',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'FQNOVEL'
WEB_SERVER_API = 'http://list.fqapi.jilulu.cn'


@CookieManager.register(namespace.lower())
def add_fqnovel_cookies(cookie=None):
    """

    Args:
        cookie (str, optional): cookie string like ``"key=name;key2=name2"``. If provided, use it. \
                                Otherwise, get new cookie by re-login.
    """

    def token_exist(browser):
        cookies = browser.get_cookies()
        return any(a['name'].startswith('Hm_lpvt') for a in cookies)

    info = CookieManager.load_info(namespace.lower())
    if cookie is None:
        browser = webdriver.Chrome()
        browser.get('https://fanqienovel.com/')
        browser.find_element(value='user-login', by=By.CLASS_NAME).find_element(value='a', by=By.TAG_NAME).click()
        browser.find_element(value='form-title-normal', by=By.CLASS_NAME).click()
        browser.find_element(value='username', by=By.NAME).send_keys(info.get('name', ''))
        browser.find_element(value='password', by=By.NAME).send_keys(info.get('password', ''))
        browser.find_element(value='sso_submit').click()
        WebDriverWait(browser, timeout=300).until(token_exist)
        cookie = ';'.join(f"{a['name']}={a['value']}" for a in browser.get_cookies())
        browser.quit()
        logger.info('Login succeeded.')
    return cookie


@RequestApi.register(namespace)
class FqNovelApi(RequestApi):
    """
    Use the xposed module and start the web service to get the chapter content

    When using the emulator from Android Studio:
    * open web server on FQWeb app on the emulator
    * make sure ``adb`` is installed and forward the port to local machine.

    References:
        * xposed module: https://github.com/fengyuecanzhu/FQWeb/tree/master
        * web service: https://telegra.ph/FQWeb-07-18
        * port forwarding: https://developer.android.com/tools/adb#forwardports
    """
    CATALOGUE_WEB_API = "https://fanqienovel.com/page/{req.book_id}"
    CATALOGUE_APP_API = f"{WEB_SERVER_API}/catalog"
    CHAPTER_WEB_API = "https://fanqienovel.com/reader/{req.item_id}"
    CHAPTER_APP_API = f"{WEB_SERVER_API}/content"
    SEARCH_APP_API = 'http://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/'
    ENCODING = 'utf-8'

    @dataclass
    class ChapterRequest(ChapterRequest):
        item_id: int
        title: Optional[str] = None

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        book_id: int

        @staticmethod
        def search_for(keywords, take=0):
            params = {
                'aid': 13,
                'q': keywords,
                'offset': (take // 10) * 10
            }
            idx = take % 10
            res = RequestsTool.request_and_json(
                FqNovelApi.SEARCH_APP_API,
                method='GET',
                encoding=FqNovelApi.ENCODING,
                request_kwargs=dict(params=params)
            )
            items = res['data']['ret_data']
            if len(items) <= idx:
                return None
            return FqNovelApi.CatalogueRequest(int(items[idx]['book_id']))

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    def __init__(self, web_service_port=9999):
        super().__init__()
        self.port = web_service_port
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Danger hiptop 3.4; U; AvantGo 3.2)",
            'cookie': self.cookies
        }

    # ====================== Get chapter ===========================
    @staticmethod
    def _parse_last_int(url, spliter):
        try:
            pure_url = url.split('?')[0]
            integer = int(pure_url.split(spliter)[-1])
            return integer
        except Exception as e:
            raise ValueError(f'The URL should be formatted as: `http*<spliter><integer>?*`')

    @staticmethod
    def _parse_title(raw):
        return raw.split('章', maxsplit=1)[-1].strip()

    @staticmethod
    def _parse_from_url_request(req):
        item_id = FqNovelApi._parse_last_int(req.url, 'reader/')
        return FqNovelApi.ChapterRequest(req.is_first, item_id, req.title)

    def _preprocess_chapter_app(self, req):
        return {
            'item_id': req.item_id,
        }

    @staticmethod
    def _parse_chapter_app(req, item):
        if int(item.get('code', '0')) != 0:
            return None, None
        next_item = item['data']['novel_data']['next_item_id']
        title = FqNovelApi._parse_title(item['data']['title'])
        content = "\n".join(map(str.strip, item['data']['content'].split('\n')))
        next = FqNovelApi.ChapterRequest(req.is_first, int(next_item)) if next_item else None
        return Chapter(title, content), next

    def get_chapter_app(self, req):
        item = RequestsTool.request_and_json(
            FqNovelApi.CHAPTER_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req))
        )
        return FqNovelApi._parse_chapter_app(req, item['data'])

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or FqNovelApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, FqNovelApi.ChapterRequest=None)``. If ``FqNovelApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = FqNovelApi._parse_from_url_request(req)
        return self.get_chapter_app(req)

    async def get_chapter_app_async(self, session, req):
        item = await RequestsTool.request_and_json_async(
            session,
            FqNovelApi.CHAPTER_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req)))
        return FqNovelApi._parse_chapter_app(req, item['data'])

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or FqNovelApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, FqNovelApi.ChapterRequest=None)``. If ``FqNovelApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = FqNovelApi._parse_from_url_request(req)
        return await self.get_chapter_app_async(session, req)

    # ====================== Get chapter list ===========================
    @staticmethod
    def _parse_from_url_catalogue_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            FqNovelApi.CatalogueRequest
        """
        try:
            return FqNovelApi.CatalogueRequest(book_id=FqNovelApi._parse_last_int(req.url, 'page/'))
        except Exception as e:
            raise ValueError(f'Invalid FQNOVEL catalogue URL: `{req.url}`')

    def get_chapter_list_web(self, req):
        def get_item(item):
            url = 'https://fanqienovel.com' + item.attrib.get('href')
            spec = FqNovelApi._parse_from_url_request(UrlChapterRequest(True, url))
            spec.title = FqNovelApi._parse_title(item.text.strip())
            return spec

        catalogue = FqNovelApi.CATALOGUE_WEB_API.format(req=req)
        d = RequestsTool.request_and_pyquery(catalogue, FqNovelApi.ENCODING,
                                             request_kwargs=dict(headers=self.headers))
        items = list(d("div.chapter-item a.chapter-item-title"))
        return list(map(get_item, items))

    def get_chapter_list_app(self, req):
        params = {
            'book_id': req.book_id,
        }
        res = RequestsTool.request_and_json(FqNovelApi.CATALOGUE_APP_API,
                                            encoding=FqNovelApi.ENCODING,
                                            request_kwargs=dict(headers=self.headers, params=params))
        items = res['data']['data'].get('item_data_list', [])
        return [FqNovelApi.ChapterRequest(
            True,
            int(item['item_id']),
            FqNovelApi._parse_title(item['title'])
        ) for item in items]

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or FqNovelApi.CatalogueRequest):

        Returns:
            list[FqNovelApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = FqNovelApi._parse_from_url_catalogue_request(req)
        try:
            chapters = self.get_chapter_list_app(req)
        except Exception as e:
            chapters = self.get_chapter_list_web(req)
        return chapters

    # ====================== Get Book Info ===========================
    def get_book_info(self, req):
        if isinstance(req, (UrlBookInfoRequest, UrlCatalogueRequest)):
            req = FqNovelApi.BookInfoRequest(FqNovelApi._parse_from_url_catalogue_request(req).book_id)
        params = {
            'book_id': req.book_id,
            'aid': 1967,
            'iid': 2665637677906061,
            'app_name': 'novelapp',
            'version_code': 495
        }
        res = RequestsTool.request_and_json(FqNovelApi.CATALOGUE_APP_API,
                                            encoding=FqNovelApi.ENCODING,
                                            request_kwargs=dict(headers=self.headers, params=params))
        info = res['data']['data']['book_info']
        tags = ", ".join(map(lambda x: x['name'], json.loads(info['category_schema'])))
        return Book(
            name=info['book_name'],
            author=info['author'],
            preface=f"{info['abstract']}\n\n{tags}"
        )
