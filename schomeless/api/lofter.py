import logging
import os.path
import shutil
from dataclasses import dataclass
from typing import Optional

import requests
from pyquery import PyQuery as pq

from schomeless.api.base import RequestApi, UrlChapterRequest, UrlCatalogueRequest
from schomeless.schema import Chapter, CatalogueRequest, ChapterRequest
from schomeless.utils import RequestsTool, EnumExtension, FileSysTool

__all__ = [
    'LofterApi',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'LOFTER'
temp_path = os.path.join(BASE_DIR, '../../temp/{filename}')


class _OCR:
    ocr = None

    @classmethod
    def get_ocr(cls):
        if cls.ocr is None:
            old_logger = logger.level
            from cnocr import CnOcr
            logger.setLevel(old_logger)
            cls.ocr = CnOcr(det_model_name='naive_det')
        return cls.ocr


class LofterMediaType(EnumExtension):
    TEXT = 1


@RequestApi.register(namespace)
class LofterApi(RequestApi):
    encoding = 'utf-8'
    POST_API = "https://api.lofter.com/oldapi/post/detail.api?product=lofter-iphone-7.2.8"
    COLLECTION_API = "https://api.lofter.com/v1.1/postCollection.api?product=lofter-iphone-7.2.8"
    BLOG_API = 'https://api.lofter.com/v2.0/blogHomePage.api?product=lofter-iphone-7.2.8'
    SEARCH_API = 'https://{req.blog_domain}/search?q={req.keyword}&page={page_id}'

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

    @dataclass
    class AppApiSearchCatalogue(CatalogueRequest):
        """get chapter list from a blog"""
        keyword: str
        blog_domain: Optional[str] = None
        blog_id: Optional[int] = None

    def __init__(self, is_ocr=False):
        """

        Args:
            is_ocr (bool, optional): whether to use OCR to recognize images.
        """
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        self.is_ocr = is_ocr

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

    def get_blog_domain_name_from_id(self, blog_id):
        payload = {
            'targetblogid': blog_id,
            'checkpwd': '1',
            'method': 'getBlogInfoDetail',
            'needgetpoststat': '0',
            'returnData': '1'
        }
        res = self.send_api_request(LofterApi.BLOG_API, payload)
        return res['blogLink']

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
        return LofterApi.AppApiChapterRequest(True, int(info['blogId']), int(info['postId']))

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
        title = post['title']
        d = pq(post['content'])
        imgs = d('img')
        n = len(imgs)
        if n > 0:
            logger.warning(f"Chapter {title}: with IMG")
            if self.is_ocr:
                ocr = _OCR.get_ocr()
                for i in range(n):
                    img = imgs.eq(i)
                    url = img.attr('src')
                    filepath = temp_path.format(filename=f"{title}_img{i}{FileSysTool.File.parse(url).extension}")
                    r = requests.get(url, stream=True)
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                    out = ocr.ocr(filepath)
                    text = '<br>'.join([x['text'] for x in out])
                    img.replace_with(f"<p>{text}</p>")
                    FileSysTool.delete_path(filepath)
        return Chapter(title=title, content=d.text().strip())

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

    # ====================== Tell URL type ===========================
    def _url_to_request(self, url):
        query = RequestsTool.parse_query(url)
        collection_id = query.get('collectionId', None)
        if collection_id is not None:
            return LofterApi.AppApiCollectionCatalogue(collection_id)
        pure_url = url.split('?', maxsplit=1)[0]
        if pure_url.endswith('search') and 'q' in query:
            return LofterApi.AppApiSearchCatalogue(keyword=query['q'], blog_domain=RequestsTool.get_domain_name(url))
        return LofterApi.AppApiBlogCatalogue(blog_domain=RequestsTool.get_domain_name(url))

    # ====================== Get chapter list ===========================
    def get_collection(self, req):
        """

        Args:
            req (LofterApi.AppApiCollectionCatalogue):

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
        return [LofterApi.AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]

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
            chapters += [LofterApi.AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]
            if add < limit:
                break
            payload['offset'] += add
        return chapters

    def get_search(self, req):
        """

        Args:
            req (AppApiSearchCatalogue):

        Returns:
            list[ChapterRequest]
        """

        def valid_url(url):
            if url:
                key = f"{RequestsTool.get_domain_name(url)}/post"
                return key in url
            return False

        page_id = 1
        if req.blog_domain is None:
            req.blog_domain = self.get_blog_domain_name_from_id(req.blog_id)
        reqs = []
        while True:
            url = RequestsTool.quote(LofterApi.SEARCH_API.format(req=req, page_id=page_id))
            d = RequestsTool.request_and_pyquery(url)
            urls = [(item.attrib.get('href', ''), item.text) for item in d('h2 a')]
            page_reqs = [UrlChapterRequest(True, url, txt) for url, txt in urls if valid_url(url)]
            reqs += page_reqs
            add = len(page_reqs)
            if add == 0:
                break
            page_id += 1
        return reqs[::-1]

    def get_chapter_list(self, catalogue):
        """Can provide either AppApiCollectionCatalogue, AppApiBlogCatalogue, or UrlCatalogueRequest.

        If URL is used:
        * For collection, like: ``https://www.lofter.com/front/blog/collection/share?collectionId=xxxxx``. \
          Or any URL with ``collectionId`` in query.
        * For search, like: ``https://xxxx.lofter.com/search?q={keyword}&page=xx``. \
          Or any URL route to ``search``.
        * For blog, like: ``https://xxxx.lofter.com/``. Or any URL not meeting the collection pattern. \
                          Would try to parse the domain name.

        Args:
            catalogue (CatalogueRequest):

        Returns:
            list[ChapterRequest]
        """
        if isinstance(catalogue, UrlCatalogueRequest):
            catalogue = self._url_to_request(catalogue.url)
        if isinstance(catalogue, LofterApi.AppApiBlogCatalogue):
            return self.get_blog(catalogue)
        if isinstance(catalogue, LofterApi.AppApiCollectionCatalogue):
            return self.get_collection(catalogue)
        if isinstance(catalogue, LofterApi.AppApiSearchCatalogue):
            return self.get_search(catalogue)
        assert False, f"Unsupported Catalogue Request: {catalogue}"
