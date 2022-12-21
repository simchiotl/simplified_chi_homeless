import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from pyquery import PyQuery as pq

from schomeless.api.base import RequestApi, UrlChapterRequest
from schomeless.schema import Chapter, CatalogueRequest, ChapterRequest
from schomeless.utils import RequestsTool, EnumExtension

__all__ = [
    'LofterApi',
    'AppApiChapterRequest',
    'AppApiCollectionCatalogue'
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'LOFTER'


class LofterMediaType(EnumExtension):
    TEXT = 1


@dataclass
class AppApiChapterRequest(ChapterRequest):
    """The Chapter request spec for APP API"""
    blog_id: int
    post_id: int
    title: Optional[str] = None


@dataclass
class AppApiCollectionCatalogue(CatalogueRequest):
    """The Chapter request spec for APP API"""
    blog_id: int
    post_id: int
    title: Optional[str] = None


# class PageNavigator(CatalogueRequest)
#
# @dataclass
# class LofterSearchCatalogue(CatalogueRequest):
#     keyword: str
#     page_id: int = 1
#     n_pages: Optional[int] = None
#

@RequestApi.register(namespace)
class LofterApi(RequestApi):
    encoding = 'utf-8'
    POST_API = "https://api.lofter.com/oldapi/post/detail.api?product=lofter-iphone-7.2.8"
    COLLECTION_API = "https://api.lofter.com/v1.1/postCollection.api?product=lofter-iphone-7.2.8"
    BLOG_INFO_API = 'https://api.lofter.com/v2.0/blogHomePage.api?product=lofter-iphone-7.2.8'
    BLOG_POST_API = 'https://api.lofter.com/v2.0/blogHomePage.api?product=lofter-iphone-7.2.8'

    def __init__(self):
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

    def send_api_request(self, API, payload):
        obj = RequestsTool.request_and_json(
            API, method='POST', request_kwargs=dict(data=payload, headers=self.headers)
        )
        if obj['meta']['msg']:
            logger.error(obj['meta']['msg'])
            return None
        return obj['response']

    def get_blog_id_from_domain_name(self, domain):
        payload = {
            'blogdomain': domain,
            'checkpwd': '1',
            'method': 'getBlogInfoDetail',
            'needgetpoststat': '0',
            'returnData': '1'
        }
        res = self.send_api_request(LofterApi.BLOG_INFO_API, payload)
        return int(res['blogsetting']['blogId'])

    def get_post(self, req):
        """

        Args:
            req (AppApiChapterRequest):

        Returns:
            Chapter
        """
        payload = {
            'postid': req.post_id,
            'supportposttypes': '1,2,3,4,5,6',
            'targetblogid': req.blog_id
        }
        obj = RequestsTool.request_and_json(
            LofterApi.POST_API,
            method='POST', request_kwargs=dict(data=payload, headers=self.headers)
        )
        if obj['meta']['msg']:
            logger.error(obj['meta']['msg'])
            return None
        post = obj['response']['posts'][0]['post']
        return Chapter(title=post['title'], content=pq(post['content']).text().strip())

    def get_collection(self, req):
        """

        Args:
            req (AppApiCollectionCatalogue):

        Returns:
            list[ChapterRequest]
        """
        payload = {
            'blogdomain': 'jinjiang-sucks.lofter.com',
            'blogid': '513533062',
            'collectionid': '3930971',
            'limit': '25',
            'method': 'getCollectionDetail',
            'offset': '50',
            'order': '1',
            'subscribeBlogId': '537034581'
        }
        obj = RequestsTool.request_and_json(
            LofterApi.COLLECTION_API,
            method='POST', request_kwargs=dict(data=payload, headers=self.headers)
        )
        if obj['meta']['msg']:
            logger.error(obj['meta']['msg'])
            return None
        post = obj['response']['posts'][0]['post']
        return Chapter(title=post['title'], content=pq(post['content']).text().strip())

    @staticmethod
    def _app_spec_from_html(html):
        """

        Args:
            html (str):

        Returns:
            AppApiChapterRequest
        """
        html, _ = html.split('<body', maxsplit=1)
        d = pq(html + "</html>")
        url = d('iframe#control_frame').attr('src')
        info = RequestsTool.parse_query(url)
        return AppApiChapterRequest(True, int(info['blogId']), int(info['postId']))

    def _url_spec_to_app_spec(self, url_req):
        """

        Args:
            url_req (UrlChapterRequest):

        Returns:
            AppApiChapterRequest
        """
        html = RequestsTool.request(url_req.url, request_kwargs=dict(headers=self.headers))
        return LofterApi._app_spec_from_html(html)

    async def _url_spec_to_app_spec_async(self, url_req):
        """

        Args:
            url_req (UrlChapterRequest):

        Returns:
            AppApiChapterRequest
        """
        html = await RequestsTool.request_async(url_req.url, request_kwargs=dict(headers=self.headers))
        return LofterApi._app_spec_from_html(html)

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest or AppApiChapterRequest):

        Returns:
            2-tuple: ``(Chapter, None)``. Don't support iterative request when using App's API
        """
        if isinstance(req, UrlChapterRequest):
            req = self._url_spec_to_app_spec(req)
        return self.get_post(req), None

    async def get_chapter_async(self, session, chapter_request):
        """

        Args:
            session (aiohttp.ClientSession):
            chapter_request (UrlChapterRequest or AppApiChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest=None)``. If ``ChapterRequest`` is None, no next chapter.
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
