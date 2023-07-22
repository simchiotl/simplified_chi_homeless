import json
import os.path
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver

from schomeless.schema import ChapterRequest, CatalogueRequest, BookInfoRequest
from schomeless.utils import Registerable, EnumExtension

__all__ = [
    'RequestApi',
    'UrlChapterRequest',
    'UrlCatalogueRequest',
    'UrlBookInfoRequest',
    'ReloginSettings',
    'CookieManager',
    'driver'
]

BASE_DIR = os.path.dirname(__file__)


class RequestApi(metaclass=Registerable):
    def get_chapter(self, chapter_request):
        """Get one page

        Args:
            chapter_request (ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest=None)``. If ``ChapterRequest`` is None, no next chapter.
        """
        raise NotImplementedError("`get_chapter`")

    async def get_chapter_async(self, session, chapter_request):
        """

        Args:
            session (aiohttp.ClientSession):
            chapter_request (ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest=None)``. If ``ChapterRequest`` is None, no next chapter.
        """
        raise NotImplementedError("`get_chapter_async`")

    def get_chapter_list(self, catalogue_request):
        """

        Args:
            catalogue_request (CatalogueRequest):

        Returns:
            list[ChapterRequest]
        """
        raise NotImplementedError("`get_chapter_list`")

    def get_book_info(self, book_info_request):
        """

        Args:
            book_info_request (BookInfoRequest):

        Returns:
            Book
        """
        raise NotImplementedError("`get_book_info`")


@dataclass
class UrlChapterRequest(ChapterRequest):
    url: str
    title: Optional[str] = None


@dataclass
class UrlCatalogueRequest(CatalogueRequest):
    url: str


@dataclass
class UrlBookInfoRequest(BookInfoRequest):
    url: str


class ReloginSettings(EnumExtension):
    NONE = 0
    WHEN_NOT_EXIST = 1
    ALWAYS = 2


class CookieManager(metaclass=Registerable):
    ACCOUNT_PATH = os.path.join(BASE_DIR, '../../resources/accounts/{name}.json')

    @classmethod
    def load_info(cls, name):
        info_path = CookieManager.ACCOUNT_PATH.format(name=name)
        with open(info_path, 'r') as fobj:
            info = json.load(fobj)
        return info

    @classmethod
    def get_field(cls, name, path):
        obj = cls.load_info(name)
        for field in path:
            obj = obj.get(field, {})
            if not isinstance(obj, dict):
                return obj
        return obj

    @classmethod
    def get_cookie(cls, name, relogin_settings=ReloginSettings.NONE):
        info = cls.load_info(name)
        cookies = info.get('cookies', None)
        if relogin_settings == ReloginSettings.ALWAYS or (
                cookies is None and relogin_settings == ReloginSettings.WHEN_NOT_EXIST):
            info = CookieManager.set_cookie(name)
        return info.get('cookies', None)

    @classmethod
    def set_cookie(cls, name, cookie=None):
        info_path = CookieManager.ACCOUNT_PATH.format(name=name)
        info = cls.load_info(name)
        info['cookies'] = CookieManager[name](cookie)
        with open(info_path, 'w') as fobj:
            json.dump(info, fobj, indent=2)
        return info

    @staticmethod
    def parse_cookie(cookie):
        items = [tuple(map(str.strip, item.split('='))) for item in cookie.split(';')]
        return {k: v for k, v in items}


class Browser:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ins = None

    def get_browser(self):
        if self.ins is None:
            self.ins = webdriver.Chrome()
        return self.ins

    def __del__(self):
        if self.ins is not None:
            self.ins.quit()


driver = Browser()
