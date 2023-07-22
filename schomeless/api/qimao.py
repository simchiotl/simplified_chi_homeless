import base64
import logging
import os.path
from dataclasses import dataclass
from typing import Optional
import cchardet

import Crypto.Cipher.AES
from pyquery import PyQuery
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager, UrlBookInfoRequest
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest, BookInfoRequest, Book
from schomeless.utils import RequestsTool, EncodingTool

__all__ = [
    'QimaoApi',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'QIMAO'

INTERNAL_ENCODING = 'utf-8'


@RequestApi.register(namespace)
class QimaoApi(RequestApi):
    CATALOGUE_WEB_API = "https://www.qimao.com/shuku/{req.book_id}/"
    CATALOGUE_APP_API = "https://api-ks.wtzw.com/api/v1/chapter/chapter-list"
    CHAPTER_WEB_API = "https://www.qimao.com/shuku/{req.book_id}-{req.chapter_id}/"
    CHAPTER_APP_API = "https://api-ks.wtzw.com/api/v1/chapter/content"
    BOOK_INFO_API = 'https://api-bc.wtzw.com/api/v1/reader/detail'
    ENCODING = 'utf-8'

    @dataclass
    class ChapterRequest(ChapterRequest):
        book_id: int
        chapter_id: int
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
                QimaoApi.SEARCH_APP_API,
                method='GET',
                encoding=QimaoApi.ENCODING,
                request_kwargs=dict(params=params)
            )
            items = res['data']['ret_data']
            if len(items) <= idx:
                return None
            return QimaoApi.CatalogueRequest(int(items[idx]['book_id']))

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    def __init__(self):
        super().__init__()
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "platform": "android",
            "app-version": "71900",
            'application-id': 'com.kmxs.reader',
            'sign': EncodingTool.MD5("app-version=71900application-id=com.kmxs.readerplatform=androidd3dGiJc651gSQ8w1"),
            'user-agent': 'webviewversion/0'
        }

    # ====================== Get chapter ===========================
    @staticmethod
    def _parse_title(raw):
        return raw.split('章', maxsplit=1)[-1].strip()

    @staticmethod
    def _decrypt(content):
        data, iv = content[32:], content[:32]
        key = EncodingTool.from_hex('32343263636238323330643730396531')
        iv = EncodingTool.from_hex(iv)
        aes = AES.new(key, AES.MODE_CBC, iv)
        data_bytes = EncodingTool.from_hex(data)
        decrypted_bytes = aes.decrypt(data_bytes)
        return decrypted_bytes.decode(INTERNAL_ENCODING)

    @staticmethod
    def _parse_from_url_request(req):
        book_id, chap_id = req.url.strip('/').split('/')[-1].split('-')
        return QimaoApi.ChapterRequest(req.is_first, int(book_id), int(chap_id), req.title)

    def _preprocess_chapter_app(self, req):
        sign = EncodingTool.MD5(f"chapterId={req.chapter_id}id={req.book_id}d3dGiJc651gSQ8w1")
        return {
            'chapterId': req.chapter_id,
            'id': req.book_id,
            'sign': sign
        }

    @staticmethod
    def _parse_chapter_app(req, item):
        payload = item.get('data', {}).get('content', None)
        if payload is None:
            return None, None
        txt = base64.b64decode(payload).hex()
        content = QimaoApi._decrypt(txt).strip()
        return Chapter(req.title, content), None

    def get_chapter_app(self, req):
        item = RequestsTool.request_and_json(
            QimaoApi.CHAPTER_APP_API,
            encoding=QimaoApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req))
        )
        return QimaoApi._parse_chapter_app(req, item)

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or QimaoApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, QimaoApi.ChapterRequest=None)``. If ``QimaoApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = QimaoApi._parse_from_url_request(req)
        return self.get_chapter_app(req)

    async def get_chapter_app_async(self, session, req):
        item = await RequestsTool.request_and_json_async(
            session,
            QimaoApi.CHAPTER_APP_API,
            encoding=QimaoApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req)))
        return QimaoApi._parse_chapter_app(req, item)

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or QimaoApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, QimaoApi.ChapterRequest=None)``. If ``QimaoApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = QimaoApi._parse_from_url_request(req)
        return await self.get_chapter_app_async(session, req)

    # ====================== Get chapter list ===========================
    @staticmethod
    def _parse_from_url_catalogue_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            QimaoApi.CatalogueRequest
        """
        try:
            return QimaoApi.CatalogueRequest(book_id=int(req.url.strip('/').split('/')[-1]))
        except Exception as e:
            raise ValueError(f'Invalid FQNOVEL catalogue URL: `{req.url}`')

    def get_chapter_list_app(self, req):
        sign = EncodingTool.MD5(f'id={req.book_id}d3dGiJc651gSQ8w1')
        params = {
            'id': req.book_id,
            'sign': sign
        }
        res = RequestsTool.request_and_json(QimaoApi.CATALOGUE_APP_API,
                                            encoding=QimaoApi.ENCODING,
                                            request_kwargs=dict(headers=self.headers, params=params))
        items = res['data'].get('chapter_lists', [])
        return [QimaoApi.ChapterRequest(
            True,
            req.book_id,
            int(item['id']),
            QimaoApi._parse_title(item['title'])
        ) for item in items]

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or QimaoApi.CatalogueRequest):

        Returns:
            list[QimaoApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = QimaoApi._parse_from_url_catalogue_request(req)
        return self.get_chapter_list_app(req)

    # ====================== Get Book Info ===========================
    def get_book_info(self, req):
        if isinstance(req, (UrlBookInfoRequest, UrlCatalogueRequest)):
            req = QimaoApi.BookInfoRequest(QimaoApi._parse_from_url_catalogue_request(req).book_id)
        params = {
            'id': req.book_id,
            'ab_type': 2
        }
        res = RequestsTool.request_and_json(QimaoApi.BOOK_INFO_API,
                                            encoding=QimaoApi.ENCODING,
                                            request_kwargs=dict(headers=self.headers, params=params))
        info = res['data']
        return Book(
            name=info['title'],
            author=info['author'],
            preface=f"{info['intro']}"
        )
