import base64
import json
import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from Crypto.Cipher import DES
from Crypto.Util.Padding import unpad
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest
from schomeless.utils import RequestsTool, EncodingTool

__all__ = [
    'JjwxcApi',
    'add_jjwxc_cookies',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'JJWXC'

# CONSTANTS
VIP_ERROR_WEB = "VIP chapters cannot be requested from Web API!"
VIP_ERROR_APP = "VIP chapters require valid token!"
INTERNAL_ENCODING = 'utf-8'
KEY_HARDCODE = "KW8Dvm2N"
IV_HARDCODE = "1ae2c94b"


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
    """Token MUST be get from Android app"""
    CATALOGUE_WEB_API = "https://www.jjwxc.net/onebook.php?novelid={req.novel_id}"
    CATALOGUE_APP_API = "https://app.jjwxc.net/androidapi/chapterList?novelId={req.novel_id}&more=0&whole=1"
    CHAPTER_WEB_API = "https://my.jjwxc.net/onebook{req.web_suffix}.php?novelid={req.novel_id}&chapterid={req.chapter_id}"
    CHAPTER_APP_API = "https://app.jjwxc.org/androidapi/chapterContent"
    WEB_ENCODING = 'gb18030'
    APP_ENCODING = 'ascii'
    APP_VERSION = 379

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
            'Referer': f'http://android.jjwxc.net?v={JjwxcApi.APP_VERSION}',
            "user-agent": "JINJIANG-iOS/5.6.5 (com.jieruitech1.JINGJIANG-iOS; build:570; iOS iPhone15,2 17.5.1 Alamofire/5.4.4"
            # "user-agent": "Mozilla/5.0 (Linux; Android 14; iPA2375 Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.134 Safari/537.36/JINJIANG-Android/379(iPA2375;Scale/2.5;isHarmonyOS/false)"
        }
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.token = CookieManager.get_field(namespace.lower(), ['token'])

    @staticmethod
    def _parse_from_url_request(req):
        args = RequestsTool.parse_query(req.url)
        return JjwxcApi.ChapterRequest(
            req.is_first,
            int(args['novelid']),
            int(args['chapterid']),
            'vip' in req.url,
            req.title
        )

    def _preprocess_chapter_web(self, req):
        assert not req.is_vip, VIP_ERROR_WEB
        url = JjwxcApi.CHAPTER_WEB_API.format(req=req)
        return url, self.headers

    @staticmethod
    def _decrypt(raw, key=KEY_HARDCODE, iv=IV_HARDCODE):
        key = key.encode(INTERNAL_ENCODING)
        iv = iv.encode(INTERNAL_ENCODING)
        des = DES.new(key, DES.MODE_CBC, iv)
        decrypted = des.decrypt(base64.b64decode(raw.encode(INTERNAL_ENCODING)))
        return unpad(decrypted, DES.block_size).decode('utf-8')

    @staticmethod
    def _parse_key_from_headers(content, headers):
        accesskey = headers.get('Accesskey')
        keyString = headers.get('Keystring')
        accesskeyLen = len(accesskey)
        v9 = 0
        v6 = str(ord(accesskey[accesskeyLen - 1]))

        for i in range(accesskeyLen):
            v9 += ord(accesskey[i])
        v15 = v9 % len(keyString)

        v17 = int(v9 / 65)
        v18 = len(keyString)
        if v17 + v15 > v18:
            v43 = keyString[v15:(v18 - v15) + v15]
        else:
            v43 = keyString[v15:v17 + v15]

        v32 = len(content)
        dest = ''
        if int(v6) & 1:
            v38 = content[v32 - 12:v32]
            dest = content[0:v32 - 12]

        else:
            v38 = content[0:12]
            dest = content[12:len(content)]

        key = EncodingTool.MD5(v43 + v38)[0:8]
        iv = EncodingTool.MD5(v38)[0:8]
        return key, iv, dest

    @staticmethod
    def _decrypt_content(text, headers=None):
        key, iv, content = KEY_HARDCODE, IV_HARDCODE, text
        if headers is not None:
            key, iv, content = JjwxcApi._parse_key_from_headers(text, headers)
        return JjwxcApi._decrypt(content, key, iv)

    @staticmethod
    def _parse_chapter_web(req, url, d):
        block = d('div.novelbody:first > div')
        title = block('h2').text()
        next_url = d('.noveltitle').eq(1).find('a:last').attr('href')
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
            next = JjwxcApi._parse_from_url_request(UrlChapterRequest(True, next_url))
        return Chapter(title, content), next

    def get_chapter_web(self, req):
        url, headers = self._preprocess_chapter_web(req)
        d = RequestsTool.request_and_pyquery(url, JjwxcApi.WEB_ENCODING, request_kwargs=dict(headers=headers))
        return JjwxcApi._parse_chapter_web(req, url, d)

    def _preprocess_chapter_app(self, req):
        assert not req.is_vip or (self.token and len(self.token.split('_')[-1]) == 32), VIP_ERROR_APP
        params = {
            'novelId': req.novel_id,
            'chapterId': req.chapter_id,
            'versionCode': JjwxcApi.APP_VERSION,
            'token': self.token
        }
        return params, self.headers

    @staticmethod
    def _parse_chapter_app(req, res, res_headers):
        item = None
        try:
            item = json.loads(res)
        except:
            item = json.loads(JjwxcApi._decrypt_content(res, res_headers))
        if item is None or item.get('message', '') == '章节不存在':
            return None, None
        title = item['chapterName']
        content = item['content']
        if 'content' in item['encryptField']:
            content = JjwxcApi._decrypt(content)
        content = '\n'.join([l.strip() for l in content.split('\n')])
        next = JjwxcApi.ChapterRequest(req.is_first, req.novel_id, req.chapter_id + 1, req.is_vip)
        return Chapter(title, content), next

    def get_chapter_app(self, req):
        params, headers = self._preprocess_chapter_app(req)
        res, res_headers = RequestsTool.request(
            JjwxcApi.CHAPTER_APP_API,
            encoding=JjwxcApi.APP_ENCODING,
            request_kwargs=dict(headers=headers, params=params),
            include_headers=True
        )
        return JjwxcApi._parse_chapter_app(req, res, res_headers)

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or JjwxcApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcApi.ChapterRequest=None)``. If ``JjwxcApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = JjwxcApi._parse_from_url_request(req)
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
        params, headers = self._preprocess_chapter_app(req)
        item, res_headers = await RequestsTool.request_async(session, JjwxcApi.CHAPTER_APP_API,
                                                             encoding=JjwxcApi.APP_ENCODING,
                                                             request_kwargs=dict(headers=headers, params=params),
                                                             include_headers=True)
        return JjwxcApi._parse_chapter_app(req, item, res_headers)

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or JjwxcApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcApi.ChapterRequest=None)``. If ``JjwxcApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = JjwxcApi._parse_from_url_request(req)
        if req.is_vip:
            try:
                return await self.get_chapter_app_async(session, req)
            except Exception as e:
                pass
        return await self.get_chapter_web_async(session, req)

    # ====================== Get chapter list ===========================
    @staticmethod
    def _parse_from_url_catalogue_request(req):
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
            spec = JjwxcApi._parse_from_url_request(UrlChapterRequest(True, url, item.text.strip()))
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
                                        item['chaptername']) for item in items if item['chaptertype'] == '0']

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or JjwxcApi.CatalogueRequest):

        Returns:
            list[JjwxcApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = JjwxcApi._parse_from_url_catalogue_request(req)
        try:
            chapters = self.get_chapter_list_app(req)
        except Exception as e:
            chapters = self.get_chapter_list_web(req)
        return chapters
