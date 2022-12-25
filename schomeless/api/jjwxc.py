import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest
from schomeless.utils import RequestsTool

__all__ = [
    'JjwxcApi',
    'add_jjwxc_cookies',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'JJWXC'

# CONSTANTS
VIP_ERROR_WEB = "VIP chapters cannot be requested from Web API!"
VIP_ERROR_APP = "VIP chapters require valid cookies! Use `CookieManager.set_cookie(\"jjwxc\")` to add cookies"


@CookieManager.register(namespace.lower())
def add_jjwxc_cookies(cookie=None):
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
class JjwxcApi(RequestApi):
    CATALOGUE_WEB_API = "https://www.jjwxc.net/onebook.php?novelid={req.novel_id}"
    CATALOGUE_APP_API = "https://app.jjwxc.net/androidapi/chapterList?novelId={req.novel_id}&more=0&whole=1"
    CHAPTER_WEB_API = "https://my.jjwxc.net/onebook{req.web_suffix}.php?novelid={req.novel_id}&chapterid={req.chapter_id}"
    CHAPTER_APP_API = "https://app.jjwxc.net/androidapi/chapterContent?novelId={req.novel_id}&chapterId={req.chapter_id}"
    WEB_ENCODING = 'gb18030'
    APP_ENCODING = 'ascii'

    @dataclass
    class ChapterRequest(ChapterRequest):
        novel_id: int
        chapter_id: int
        is_vip: bool
        title: Optional[str] = None

        @property
        def web_suffix(self):
            return '_vip' if self.is_vip else ''

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        novel_id: int

    def __init__(self):
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        self.cookies = CookieManager.get_cookie(namespace.lower())

    @staticmethod
    def _parse_request_from_chapter_url(url):
        args = RequestsTool.parse_query(url)
        return JjwxcApi.ChapterRequest(True, int(args['novelid']), int(args['chapterid']), 'vip' in url)

    def _preprocess_chapter_web(self, req):
        assert not req.is_vip, VIP_ERROR_WEB
        url = JjwxcApi.CHAPTER_WEB_API.format(req=req)
        return url, self.headers

    @staticmethod
    def _parse_chapter_web(req, url, d):
        block = d('div.noveltext')
        title = block('h2').text()
        next_url = d('td.noveltitle').eq(2).find('a:last').attr('href')
        if req.is_vip:
            content = block('#show').next().text().strip()
            next_url = RequestsTool.get_host(url) + next_url
        else:
            block.remove('div')
            content = block.text().strip()
            next_url = os.path.join(RequestsTool.get_dirname(url), next_url)
        if next_url.split('?')[-1] == url.split('?')[-1]:
            next = None
        else:
            next = JjwxcApi._parse_request_from_chapter_url(next_url)
        return Chapter(title, content), next

    def get_chapter_web(self, req):
        url, headers = self._preprocess_chapter_web(req)
        d = RequestsTool.request_and_pyquery(url, JjwxcApi.WEB_ENCODING, request_kwargs=dict(headers=headers))
        return JjwxcApi._parse_chapter_web(req, url, d)

    def _preprocess_chapter_app(self, req):
        assert not req.is_vip or (self.cookies is not None and 'token' in self.cookies), VIP_ERROR_APP
        url = JjwxcApi.CHAPTER_APP_API.format(req=req)
        headers = self.headers
        if req.is_vip:
            headers = dict(cookie=self.cookies, **headers)
        return url, headers

    @staticmethod
    def _parse_chapter_app(req, url, item):
        title = item['chapterName']
        content = '\n'.join([l.strip() for l in item['content'].split('\n')])
        next = JjwxcApi.ChapterRequest(req.is_first, req.novel_id, req.chapter_id + 1, req.is_vip)
        return Chapter(title, content), next

    def get_chapter_app(self, req):
        url, headers = self._preprocess_chapter_app(req)
        item = RequestsTool.request_and_json(url, JjwxcApi.APP_ENCODING, request_kwargs=dict(headers=headers))
        if item.get('message', '') == '章节不存在':
            return None, None
        return JjwxcApi._parse_chapter_app(req, url, item)

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or JjwxcApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcApi.ChapterRequest=None)``. If ``JjwxcApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = JjwxcApi._parse_request_from_chapter_url(req.url)
        if req.is_vip:
            try:
                return self.get_chapter_app(req)
            except Exception as e:
                pass
        return self.get_chapter_web(req)

    async def get_chapter_web_async(self, session, req):
        url, headers = self._preprocess_chapter_web(req)
        d = await RequestsTool.request_and_pyquery_async(session, url, JjwxcApi.WEB_ENCODING,
                                                         request_kwargs=dict(headers=headers))
        return self._parse_chapter_web(req, url, d)

    async def get_chapter_app_async(self, session, req):
        url, headers = self._preprocess_chapter_app(req)
        item = await RequestsTool.request_and_json_async(session, url, JjwxcApi.APP_ENCODING,
                                                         request_kwargs=dict(headers=headers))
        return JjwxcApi._parse_chapter_app(req, url, item)

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or JjwxcApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcApi.ChapterRequest=None)``. If ``JjwxcApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = JjwxcApi._parse_request_from_chapter_url(req.url)
        if req.is_vip:
            try:
                return await self.get_chapter_app_async(session, req)
            except Exception as e:
                pass
        return await self.get_chapter_web_async(session, req)

    # ====================== Get chapter list ===========================
    @staticmethod
    def _catalogue_url_to_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            JjwxcApi.CatalogueRequest
        """
        try:
            return JjwxcApi.CatalogueRequest(novel_id=int(RequestsTool.parse_query(req.url)['novelid']))
        except Exception as e:
            raise ValueError(f'Invalid JJWXC catalogue URL: `{req.url}`')

    def get_chapter_list_web(self, req):
        def get_item(item):
            url = item.attrib.get('href', item.attrib.get('rel'))
            spec = JjwxcApi._parse_request_from_chapter_url(url)
            spec.title = item.text.strip()
            return spec

        catalogue = JjwxcApi.CATALOGUE_WEB_API.format(req=req)
        d = RequestsTool.request_and_pyquery(catalogue, JjwxcApi.WEB_ENCODING,
                                             request_kwargs=dict(headers=self.headers))
        items = list(d("tr[itemscope] span[itemprop=headline] div:first a[itemprop=url]"))
        return list(map(get_item, items))

    def get_chapter_list_app(self, req):
        catalogue = JjwxcApi.CATALOGUE_APP_API.format(req=req)
        res = RequestsTool.request_and_json(catalogue, encoding=JjwxcApi.APP_ENCODING,
                                            request_kwargs=dict(headers=self.headers))
        items = res.get('chapterlist', [])
        return [JjwxcApi.ChapterRequest(True, int(item['novelid']), int(item['chapterid']), bool(item['isvip']),
                                        item['chaptername']) for item in items]

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or JjwxcApi.CatalogueRequest):

        Returns:
            list[JjwxcApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = JjwxcApi._catalogue_url_to_request(req)
        try:
            chapters = self.get_chapter_list_app(req)
        except Exception as e:
            chapters = self.get_chapter_list_web(req)
        return chapters
