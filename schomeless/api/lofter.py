import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from pyquery import PyQuery as pq

from schomeless.api.base import RequestApi, UrlChapterRequest, UrlCatalogueRequest
from schomeless.schema import Chapter, CatalogueRequest, ChapterRequest
from schomeless.utils import RequestsTool, EnumExtension

__all__ = [
    'LofterApi',
    'AppApiChapterRequest',
    'AppApiCollectionCatalogue',
    'AppApiBlogCatalogue'
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
    """Get chapter list in a collection"""
    collection_id: int


@dataclass
class AppApiBlogCatalogue(CatalogueRequest):
    """get chapter list from a blog"""
    blog_domain: Optional[str] = None
    blog_id: Optional[int] = None
    post_per_page: int = 25


@RequestApi.register(namespace)
class LofterApi(RequestApi):
    encoding = 'utf-8'
    POST_API = "https://api.lofter.com/oldapi/post/detail.api?product=lofter-iphone-7.2.8"
    COLLECTION_API = "https://api.lofter.com/v1.1/postCollection.api?product=lofter-iphone-7.2.8"
    BLOG_API = 'https://api.lofter.com/v2.0/blogHomePage.api?product=lofter-iphone-7.2.8'

    def __init__(self):
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

    def send_api_request(self, API, payload):
        obj = RequestsTool.request_and_json(
            API, method='POST', request_kwargs=dict(data=payload, headers=self.headers)
        )
        assert not obj['meta']['msg'], obj['meta']['msg']
        return obj['response']

    async def send_api_request_async(self, session, API, payload):
        obj = await RequestsTool.request_and_json_async(
            session, API, method='POST', request_kwargs=dict(data=payload, headers=self.headers)
        )
        assert not obj['meta']['msg'], obj['meta']['msg']
        return obj['response']

    def get_blog_id_from_domain_name(self, domain):
        payload = {
            'blogdomain': domain,
            'checkpwd': '1',
            'method': 'getBlogInfoDetail',
            'needgetpoststat': '0',
            'returnData': '1'
        }
        res = self.send_api_request(LofterApi.BLOG_API, payload)
        return int(res['blogsetting']['blogId'])

    @staticmethod
    def _chapter_app_spec_from_html(html):
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

    def _chapter_url_spec_to_app_spec(self, url_req):
        """

        Args:
            url_req (UrlChapterRequest):

        Returns:
            AppApiChapterRequest
        """
        html = RequestsTool.request(url_req.url, request_kwargs=dict(headers=self.headers))
        return LofterApi._chapter_app_spec_from_html(html)

    async def _chapter_url_spec_to_app_spec_async(self, session, url_req):
        """

        Args:
            url_req (UrlChapterRequest):

        Returns:
            AppApiChapterRequest
        """
        html = await RequestsTool.request_async(session, url_req.url, request_kwargs=dict(headers=self.headers))
        return LofterApi._chapter_app_spec_from_html(html)

    def get_post_payload(self, req):
        return {
            'postid': req.post_id,
            'supportposttypes': '1,2,3,4,5,6',
            'targetblogid': req.blog_id
        }

    def get_post_postprocess(self, res):
        post = res['posts'][0]['post']
        return Chapter(title=post['title'], content=pq(post['content']).text().strip())

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest or AppApiChapterRequest): Could be a url like: \
                                                             ``https://xxx.lofter.com/post/xxxxxx_xxxxxxxxx``

        Returns:
            2-tuple: ``(Chapter, None)``. Don't support iterative request when using App's API
        """
        if isinstance(req, UrlChapterRequest):
            req = self._chapter_url_spec_to_app_spec(req)
        res = self.send_api_request(LofterApi.POST_API, self.get_post_payload(req))
        return self.get_post_postprocess(res), None

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest or AppApiChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest=None)``. If ``ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = await self._chapter_url_spec_to_app_spec_async(session, req)
        res = await self.send_api_request_async(session, LofterApi.POST_API, self.get_post_payload(req))
        return self.get_post_postprocess(res), None

    # ====================== Get chapter list ===========================
    def get_collection(self, req):
        """

        Args:
            req (AppApiCollectionCatalogue):

        Returns:
            list[ChapterRequest]
        """
        payload = {
            'collectionid': req.collection_id,
            'limit': 1,
            'method': 'getCollectionDetail',
            'offset': 0,
            'order': 1,
        }
        res = self.send_api_request(LofterApi.COLLECTION_API, payload)
        total = res['collection']['postCount']
        payload['limit'] = total
        res = self.send_api_request(LofterApi.COLLECTION_API, payload)
        items = [item['post'] for item in res['items']]
        return [AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]

    def get_blog(self, req):
        """

        Args:
            req (AppApiBlogCatalogue):

        Returns:
            list[ChapterRequest]
        """
        limit = req.post_per_page
        payload = {
            'method': 'getPostLists',
            'limit': limit,
            'offset': 0,
            'order': 0,
            'supportposttypes': '1,2,3,4,5,6',
        }
        if req.blog_id is not None:
            payload['targetblogid'] = req.blog_id
        if req.blog_domain is not None:
            payload['blogdomain'] = req.blog_domain
        assert 'targetblogid' in payload or 'blogdomain' in payload, "Either blog ID or blog domain name is required!"
        chapters = []
        while True:
            res = self.send_api_request(LofterApi.BLOG_API, payload)
            items = [item['post'] for item in res['posts']]
            add = len(items)
            chapters += [AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]
            if add < limit:
                break
            payload['offset'] += add
        return chapters

    def get_chapter_list(self, catalogue):
        """Can provide either AppApiCollectionCatalogue, AppApiBlogCatalogue, or UrlCatalogueRequest.

        If URL is used:
        * For collection, like: ``https://www.lofter.com/front/blog/collection/share?collectionId=xxxxx``. \
          Or any URL with ``collectionId`` in query.
        * For blog, like: ``https://xxxx.lofter.com/``. Or any URL not meeting the collection pattern. \
                          Would try to parse the domain name.

        Args:
            catalogue (CatalogueRequest):

        Returns:
            list[ChapterRequest]
        """
        if isinstance(catalogue, UrlCatalogueRequest):
            query = RequestsTool.parse_query(catalogue.url)
            collection_id = query.get('collectionId', None)
            if collection_id is not None:
                # collection
                catalogue = AppApiCollectionCatalogue(collection_id)
            else:
                # blog
                pass
        if isinstance(catalogue, AppApiBlogCatalogue):
            return self.get_blog(catalogue)
        if isinstance(catalogue, AppApiCollectionCatalogue):
            return self.get_collection(catalogue)
        assert False, f"Unsupported Catalogue Request: {catalogue}"
