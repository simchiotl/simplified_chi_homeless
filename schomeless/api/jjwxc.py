import json
import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver

from schomeless.api.base import RequestApi
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest
from schomeless.utils import LogTool, RequestsTool

__all__ = [
    'JjwxcApi',
    'WebJjwxcApi',
    'AppJjwxcApi',
    'JjwxcChapterRequest',
    'JjwxcCatalogueRequest',
    'get_jjwxc_cookies'
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'JJWXC'


def get_jjwxc_cookies(force_relogin=False):
    info_path = os.path.join(BASE_DIR, '../../resources/accounts/jjwxc.json')
    with open(info_path, 'r') as fobj:
        info = json.load(fobj)
    if not force_relogin and info.get('cookies', None):
        return info['cookies']

    browser = webdriver.Chrome()
    browser.get('https://www.jjwxc.net/')
    browser.find_element(value='jj_login').click()
    browser.find_element(value='loginname').send_keys(info['name'])
    browser.find_element(value='loginpassword').send_keys(info['password'])
    browser.find_element(value='login_registerRule').click()
    browser.find_element(value='login_cookietime').click()
    LogTool.confirm('login to JJWXC')
    info['cookies'] = ';'.join(f"{a['name']}={a['value']}" for a in browser.get_cookies())
    with open(info_path, 'w') as fobj:
        json.dump(info, fobj, indent=2)
    logger.info('Login succeeded.')


@dataclass
class JjwxcChapterRequest(ChapterRequest):
    novel_id: str
    chapter_id: str
    is_vip: bool
    title: Optional[str] = None


@dataclass
class JjwxcCatalogueRequest(CatalogueRequest):
    novel_id: str


@RequestApi.register(namespace)
class JjwxcApi(RequestApi):
    def __init__(self, cookies=None):
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        if cookies is not None:
            self.headers['cookie'] = cookies

    def chapter_url(self, chapter_request):
        """

        Args:
            chapter_request (JjwxcChapterRequest):

        Returns:
            str
        """
        raise NotImplementedError("`chapter_url`")

    def chapter_list_url(self, novel_id):
        raise NotImplementedError("`chapter_list_url`")

    def get_chapter(self, chapter_request):
        """

        Args:
            chapter_request (JjwxcChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcChapterRequest=None)``. If ``JjwxcChapterRequest`` is None, no next chapter.
        """
        raise NotImplementedError("`get_chapter`")

    async def get_chapter_async(self, session, chapter_request):
        """

        Args:
            session (aiohttp.ClientSession):
            chapter_request (JjwxcChapterRequest):

        Returns:
            2-tuple: ``(Chapter, JjwxcChapterRequest=None)``. If ``JjwxcChapterRequest`` is None, no next chapter.
        """
        raise NotImplementedError("`get_chapter_async`")

    def get_chapter_list(self, catalogue_request):
        """

        Args:
            catalogue_request (JjwxcCatalogueRequest):

        Returns:
            list[JjwxcChapterRequest]
        """
        raise NotImplementedError("`get_chapter_list_internal`")


@JjwxcApi.register('WEB')
class WebJjwxcApi(JjwxcApi):
    """Web 抓取方式， 只适合免费文"""
    encoding = 'gb18030'

    def chapter_url(self, req):
        return f"https://my.jjwxc.net/onebook{'_vip' if req.is_vip else ''}.php?novelid={req.novel_id}&chapterid={req.chapter_id}"

    def chapter_list_url(self, novel_id):
        return f"https://www.jjwxc.net/onebook.php?novelid={novel_id}"

    @staticmethod
    def parse_request_from_chapter_url(url):
        args = RequestsTool.parse_query(url)
        return JjwxcChapterRequest(True, args['novelid'], args['chapterid'], 'vip' in url)

    def get_chapter_list(self, catalogue_req):
        def get_item(item):
            url = item.attrib.get('href', item.attrib.get('rel'))
            spec = WebJjwxcApi.parse_request_from_chapter_url(url)
            spec.title = item.text.strip()
            return spec

        catalogue = self.chapter_list_url(catalogue_req.novel_id)
        d = RequestsTool.request_and_pyquery(catalogue, WebJjwxcApi.encoding)
        items = list(d("tr[itemscope] span[itemprop=headline] div:first a[itemprop=url]"))
        return list(map(get_item, items))

    def _parse_chapter(self, req, url, d):
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
            next = WebJjwxcApi.parse_request_from_chapter_url(next_url)
        return Chapter(title, content), next

    def get_chapter(self, req):
        url = self.chapter_url(req)
        d = RequestsTool.request_and_pyquery(url, WebJjwxcApi.encoding)
        return self._parse_chapter(req, url, d)

    async def get_chapter_async(self, session, req):
        url = self.chapter_url(req)
        d = await RequestsTool.request_and_pyquery_async(session, url, WebJjwxcApi.encoding)
        return self._parse_chapter(req, url, d)


@JjwxcApi.register('APP')
class AppJjwxcApi(JjwxcApi):
    """Web 抓取方式， 只适合自己买了的V文"""
    encoding = 'ascii'

    def chapter_url(self, req):
        return f"https://app.jjwxc.net/androidapi/chapterContent?novelId={req.novel_id}&chapterId={req.chapter_id}"

    def chapter_list_url(self, novel_id):
        return f"https://app.jjwxc.net/androidapi/chapterList?novelId={novel_id}&more=0&whole=1'"

    def get_chapter_list(self, catalogue_req):
        catalogue = self.chapter_list_url(catalogue_req.novel_id)
        items = RequestsTool.request_and_json(catalogue, encoding=AppJjwxcApi.encoding).get('chapterlist', [])
        return [JjwxcChapterRequest(True, item['novelid'], item['chapterid'], bool(item['isvip']), item['chaptername'])
                for item in items]

    def _parse_chapter(self, item):
        title = item['chapterName']
        content = '\n'.join([l.strip() for l in item['content'].split('\n')])
        return Chapter(title, content), None

    def get_chapter(self, req):
        url = self.chapter_url(req)
        item = RequestsTool.request_and_json(url, AppJjwxcApi.encoding,
                                             request_kwargs=dict(headers=self.headers))
        return self._parse_chapter(item)

    async def get_chapter_async(self, session, req):
        url = self.chapter_url(req)
        item = await RequestsTool.request_and_json_async(session, url, AppJjwxcApi.encoding,
                                                         request_kwargs=dict(headers=self.headers))
        return self._parse_chapter(item)
