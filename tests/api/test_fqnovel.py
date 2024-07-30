import asyncio
import json
import os.path
import unittest

import aiohttp

from schomeless.api.base import UrlCatalogueRequest, CookieManager, ReloginSettings
from schomeless.api.fqnovel import *

BASE_DIR = os.path.dirname(__file__)


class TestFqNovelApi(unittest.TestCase):

    def setUp(self):
        self.api = FqNovelApi()
        self.info_path = os.path.join(BASE_DIR, '../../resources/accounts/fqnovel.json')
        self.backup = self.info_path[:-5] + "-backup.json"
        with open(self.backup, 'w') as wobj, open(self.info_path, 'r') as fobj:
            json.dump(json.load(fobj), wobj)

    def set_cookies(self, cookie=None):
        with open(self.info_path, 'r') as fobj:
            info = json.load(fobj)
        if cookie is None and 'cookies' in info:
            info.pop('cookies')
        else:
            info['cookies'] = cookie
        with open(self.info_path, 'w') as fobj:
            json.dump(info, fobj)

    def test_cookies(self):
        # return cookies when exists
        CookieManager.set_cookie('fqnovel', '123')
        self.assertEqual(CookieManager.get_cookie('fqnovel'), '123')
        self.set_cookies(None)
        self.assertIsNone(CookieManager.get_cookie('fqnovel'))

        # add when not exists
        # CookieManager.get_cookie('fqnovel', ReloginSettings.WHEN_NOT_EXIST)
        CookieManager.set_cookie('fqnovel', '123')
        self.assertEqual(CookieManager.get_cookie('fqnovel', ReloginSettings.WHEN_NOT_EXIST), '123')

        # always
        # self.assertNotEqual(CookieManager.get_cookie('fqnovel', ReloginSettings.ALWAYS), '123')

    def test_url_to_request(self):
        url = 'https://fanqienovel.com/page/6969913600760613901'
        req = FqNovelApi._parse_from_url_catalogue_request(UrlCatalogueRequest(url))
        self.assertEqual(req.book_id, 6969913600760613901)

    def test_get_chapter_list(self):
        # WEB api
        req = FqNovelApi.CatalogueRequest(6969913600760613901)
        lis = self.api.get_chapter_list_web(req)
        self.assertEqual(len(lis), 980)

        # APP api
        lis = self.api.get_chapter_list_app(req)
        self.assertEqual(len(lis), 980)

        # all
        req = UrlCatalogueRequest('https://fanqienovel.com/page/6969913600760613901')
        lis = self.api.get_chapter_list(req)
        self.assertEqual(len(lis), 980)

    def test_get_chapter_web(self):
        def get_chapter_web_async(api, spec):
            async def _core():
                async with aiohttp.ClientSession() as session:
                    return await api.get_chapter_web_async(session, spec)

            return asyncio.run(_core())

        # normal chapter
        req = FqNovelApi.ChapterRequest(True, 6522339816720302596)
        chap, next = self.api.get_chapter_web(req)
        self.assertEqual(chap.title, '道尽委屈')
        chap2, next2 = self.api.get_chapter_web(next)
        self.assertEqual(chap2.title, '没事找事')

        # async
        chap_async, next_async = get_chapter_web_async(self.api, req)
        self.assertEqual(chap.title, chap_async.title)
        self.assertEqual(chap.id, chap_async.id)
        self.assertEqual(chap.content, chap_async.content)
        self.assertEqual(next, next_async)

        # error chapter
        req = FqNovelApi.ChapterRequest(True, 691270568977135174175)
        chap, next = self.api.get_chapter_web(req)
        self.assertIsNone(chap)
        self.assertIsNone(next)

    def test_get_chapter_app(self):
        # normal chapter
        req = FqNovelApi.ChapterRequest(True, 6522339815122272781)
        chap, next = self.api.get_chapter_app(req)
        self.assertEqual(chap.title, None)
        self.assertIsNone(next)

        # error chapter
        req = FqNovelApi.ChapterRequest(True, 691270568977135174175)
        chap, next = self.api.get_chapter_app(req)
        self.assertIsNone(chap)
        self.assertIsNone(next)

    def test_get_chapter(self):
        def get_chapter_async(api, spec):
            async def _core():
                async with aiohttp.ClientSession() as session:
                    return await api.get_chapter_async(session, spec)

            return asyncio.run(_core())

        # normal chapter
        req = FqNovelApi.ChapterRequest(True, 6522339818679042574)
        chap, next = self.api.get_chapter(req)
        self.assertEqual(chap.title, '没事找事')
        chap2, next2 = self.api.get_chapter(next)
        self.assertEqual(chap2.title, '嫁娶天注定')

        # async
        chap_async, next_async = get_chapter_async(self.api, req)
        self.assertEqual(chap.title, chap_async.title)
        self.assertEqual(chap.id, chap_async.id)
        self.assertEqual(chap.content, chap_async.content)
        self.assertEqual(next, next_async)

        # error chapter
        req = FqNovelApi.ChapterRequest(True, 691270568977135174175)
        chap, next = self.api.get_chapter(req)
        self.assertIsNone(chap)
        self.assertIsNone(next)

    def test_search(self):
        keywords = '惜花芷'
        req = FqNovelApi.CatalogueRequest.search_for(keywords)
        self.assertTrue(req.book_id in {7012507022671219742, 6621052928482348040})

    def test_get_book_info(self):
        req = FqNovelApi.BookInfoRequest(6971402430827203620)
        book = self.api.get_book_info(req)
        self.assertEqual(book.author, '空留')
        self.assertEqual(book.name, '幺女长乐')

    def recover_cookies(self):
        with open(self.backup, 'r') as fobj, open(self.info_path, 'w') as wobj:
            json.dump(json.load(fobj), wobj, indent=2)

    def tearDown(self):
        self.recover_cookies()
