import asyncio
import json
import os.path
import unittest

import aiohttp

from schomeless.api.base import UrlCatalogueRequest, CookieManager, ReloginSettings
from schomeless.api.jjwxc import *

BASE_DIR = os.path.dirname(__file__)


class TestJjwxcApi(unittest.TestCase):

    def setUp(self):
        self.api = JjwxcApi()
        self.info_path = os.path.join(BASE_DIR, '../../resources/accounts/jjwxc.json')
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
        CookieManager.set_cookie('jjwxc', '123')
        self.assertEqual(CookieManager.get_cookie('jjwxc'), '123')
        self.set_cookies(None)
        self.assertIsNone(CookieManager.get_cookie('jjwxc'))

        # add when not exists
        # CookieManager.get_cookie('jjwxc', ReloginSettings.WHEN_NOT_EXIST)
        CookieManager.set_cookie('jjwxc', '123')
        self.assertEqual(CookieManager.get_cookie('jjwxc', ReloginSettings.WHEN_NOT_EXIST), '123')

        # always
        # self.assertNotEqual(CookieManager.get_cookie('jjwxc', ReloginSettings.ALWAYS), '123')

    def test_get_chapter_list(self):
        def test_core(chaps_a, chaps_b, length):
            self.assertEqual(len(chaps_a), len(chaps_b))
            self.assertEqual(len(chaps_a), length)
            for a, b in zip(chaps_a, chaps_b):
                self.assertEqual(a, b)

        # from novel ID
        spec = JjwxcApi.CatalogueRequest(5539562)
        web_chaps = self.api.get_chapter_list_web(spec)
        app_chaps = self.api.get_chapter_list_app(spec)
        test_core(web_chaps, app_chaps, 156)

        # from URL
        spec = UrlCatalogueRequest(url='https://www.jjwxc.net/onebook.php?novelid=5539562')
        uni_chaps = self.api.get_chapter_list(spec)
        test_core(web_chaps, uni_chaps, 156)

    def test_get_chapter(self):
        def test_chapter(chap, next):
            self.assertIsNotNone(chap)
            self.assertEqual(next.novel_id, spec.novel_id)
            self.assertEqual(next.chapter_id, spec.chapter_id + 1)
            self.assertEqual(spec.is_vip, next.is_vip)

        def app_vip_error():
            with self.assertRaises(AssertionError) as cm:
                chap, next = self.api.get_chapter_app(spec)
            self.assertEqual(cm.exception.args[0],
                             "VIP chapters require valid token!")

        async def get_chapter_async(api, spec):
            async with aiohttp.ClientSession() as session:
                res = await api.get_chapter_app_async(session, spec)
                return res

        # free chapter
        self.api.cookies = None
        self.api.token = None
        spec = JjwxcApi.ChapterRequest(True, 5539562, 2, False)
        chap, next = self.api.get_chapter_web(spec)
        test_chapter(chap, next)
        chap2, next2 = self.api.get_chapter_app(spec)
        test_chapter(chap2, next2)
        self.assertEqual(chap, chap2)
        self.assertEqual(next, next2)

        # vip chapter
        spec = JjwxcApi.ChapterRequest(True, 5539562, 29, True)
        with self.assertRaises(AssertionError) as cm:
            chap, next = self.api.get_chapter_web(spec)
        self.assertEqual(cm.exception.args[0], "VIP chapters cannot be requested from Web API!")
        app_vip_error()
        self.api.cookies = '123'
        self.api.token = '123'
        app_vip_error()
        self.api.token = CookieManager.get_field('jjwxc', ['token'])
        chap_async, next_async = asyncio.run(get_chapter_async(self.api, spec))
        chap, next = self.api.get_chapter_app(spec)
        self.assertEqual(chap.id, chap_async.id)
        self.assertEqual(chap.content, chap_async.content)
        self.assertEqual(chap.title, chap_async.title)
        self.assertEqual(next, next_async)
        test_chapter(chap, next)

        # not exist chapter
        spec = JjwxcApi.ChapterRequest(True, 5539562, 190, True)
        chap, next = self.api.get_chapter_app(spec)
        self.assertIsNone(chap)
        self.assertIsNone(next)

    def recover_cookies(self):
        with open(self.backup, 'r') as fobj, open(self.info_path, 'w') as wobj:
            json.dump(json.load(fobj), wobj, indent=2)

    def tearDown(self):
        self.recover_cookies()
