import logging
import os.path

from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlChapterRequest
from schomeless.schema import Chapter
from schomeless.utils import RequestsTool

__all__ = [
    'ChongyaApi',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'CHONGYA'
temp_path = os.path.join(BASE_DIR, '../../temp/{filename}')


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


@RequestApi.register(namespace)
class ChongyaApi(RequestApi):
    encoding = 'utf-8'

    def __init__(self):
        """

        Args:
            is_ocr (bool, optional): whether to use OCR to recognize images.
        """
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }

    def get_post_postprocess(self, req, url, d):
        title = d('title').text().strip()
        content = d('div.content').text().strip()
        a = d('div.album-article-group:last div.next-article-title a')
        next = None
        if len(a) > 0:
            next_title = a.text().strip()
            next_url = RequestsTool.get_domain_name(url) + a.attr('href')
            next = UrlChapterRequest(True, next_url, next_title)
        return Chapter(title, content), next

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest): Could be a url like: ``https://m.chongya.com/update/xxxxxx``

        Returns:
            2-tuple: ``(Chapter, None)``. Don't support iterative request when using App's API
        """

        def chapter_exist(browser):
            try:
                e = browser.find_element(by=By.CLASS_NAME, value='content')
                return True
            except NoSuchElementException:
                return False

        browser = driver.get_browser()
        browser.get(req.url)
        WebDriverWait(browser, timeout=60).until(chapter_exist)
        d = pq(browser.page_source)
        return self.get_post_postprocess(req, req.url, d)

    # async def get_chapter_async(self, session, req):
    #     """
    #
    #     Args:
    #         session (aiohttp.ClientSession):
    #         req (UrlChapterRequest or AppApiChapterRequest):
    #
    #     Returns:
    #         2-tuple: ``(Chapter, ChapterRequest=None)``. If ``ChapterRequest`` is None, no next chapter.
    #     """
    #     d = await RequestsTool.request_and_pyquery_async(session, req.url,
    #                                                      encoding=ChongyaApi.encoding,
    #                                                      request_kwargs=dict(headers=self.headers))
    #     return self.get_post_postprocess(req, req.url, d)

    # # ====================== Tell URL type ===========================
    # def _url_to_request(self, url):
    #     query = RequestsTool.parse_query(url)
    #     collection_id = query.get('collectionId', None)
    #     if collection_id is not None:
    #         return AppApiCollectionCatalogue(collection_id)
    #     pure_url = url.split('?', maxsplit=1)[0]
    #     if pure_url.endswith('search') and 'q' in query:
    #         return AppApiSearchCatalogue(keyword=query['q'], blog_domain=RequestsTool.get_domain_name(url))
    #     return AppApiBlogCatalogue(blog_domain=RequestsTool.get_domain_name(url))
    #
    # # ====================== Get chapter list ===========================
    # def get_collection(self, req):
    #     """
    #
    #     Args:
    #         req (AppApiCollectionCatalogue):
    #
    #     Returns:
    #         list[ChapterRequest]
    #     """
    #     payload = {
    #         'collectionid': req.collection_id,
    #         'limit': 1,
    #         'method': 'getCollectionDetail',
    #         'offset': 0,
    #         'order': 1,
    #     }
    #     res = self.send_api_request(LofterApi.COLLECTION_API, payload)
    #     total = res['collection']['postCount']
    #     payload['limit'] = total
    #     res = self.send_api_request(LofterApi.COLLECTION_API, payload)
    #     items = [item['post'] for item in res['items']]
    #     return [AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]
    #
    # def get_blog(self, req):
    #     """
    #
    #     Args:
    #         req (AppApiBlogCatalogue):
    #
    #     Returns:
    #         list[ChapterRequest]
    #     """
    #     limit = req.post_per_page
    #     payload = {
    #         'method': 'getPostLists',
    #         'limit': limit,
    #         'offset': 0,
    #         'order': 0,
    #         'supportposttypes': '1,2,3,4,5,6',
    #     }
    #     if req.blog_id is not None:
    #         payload['targetblogid'] = req.blog_id
    #     if req.blog_domain is not None:
    #         payload['blogdomain'] = req.blog_domain
    #     assert 'targetblogid' in payload or 'blogdomain' in payload, "Either blog ID or blog domain name is required!"
    #     chapters = []
    #     while True:
    #         res = self.send_api_request(LofterApi.BLOG_API, payload)
    #         items = [item['post'] for item in res['posts']]
    #         add = len(items)
    #         chapters += [AppApiChapterRequest(True, obj['blogId'], obj['id'], obj['title']) for obj in items]
    #         if add < limit:
    #             break
    #         payload['offset'] += add
    #     return chapters
    #
    # def get_search(self, req):
    #     """
    #
    #     Args:
    #         req (AppApiSearchCatalogue):
    #
    #     Returns:
    #         list[ChapterRequest]
    #     """
    #
    #     def valid_url(url):
    #         if url:
    #             key = f"{RequestsTool.get_domain_name(url)}/post"
    #             return key in url
    #         return False
    #
    #     page_id = 1
    #     if req.blog_domain is None:
    #         req.blog_domain = self.get_blog_domain_name_from_id(req.blog_id)
    #     reqs = []
    #     while True:
    #         url = RequestsTool.quote(LofterApi.SEARCH_API.format(req=req, page_id=page_id))
    #         d = RequestsTool.request_and_pyquery(url)
    #         urls = [(item.attrib.get('href', ''), item.text) for item in d('h2 a')]
    #         page_reqs = [UrlChapterRequest(True, url, txt) for url, txt in urls if valid_url(url)]
    #         reqs += page_reqs
    #         add = len(page_reqs)
    #         if add == 0:
    #             break
    #         page_id += 1
    #     return reqs[::-1]
    #
    # def get_chapter_list(self, catalogue):
    #     """Can provide either AppApiCollectionCatalogue, AppApiBlogCatalogue, or UrlCatalogueRequest.
    #
    #     If URL is used:
    #     * For collection, like: ``https://www.lofter.com/front/blog/collection/share?collectionId=xxxxx``. \
    #       Or any URL with ``collectionId`` in query.
    #     * For search, like: ``https://xxxx.lofter.com/search?q={keyword}&page=xx``. \
    #       Or any URL route to ``search``.
    #     * For blog, like: ``https://xxxx.lofter.com/``. Or any URL not meeting the collection pattern. \
    #                       Would try to parse the domain name.
    #
    #     Args:
    #         catalogue (CatalogueRequest):
    #
    #     Returns:
    #         list[ChapterRequest]
    #     """
    #     if isinstance(catalogue, UrlCatalogueRequest):
    #         catalogue = self._url_to_request(catalogue.url)
    #     if isinstance(catalogue, AppApiBlogCatalogue):
    #         return self.get_blog(catalogue)
    #     if isinstance(catalogue, AppApiCollectionCatalogue):
    #         return self.get_collection(catalogue)
    #     if isinstance(catalogue, AppApiSearchCatalogue):
    #         return self.get_search(catalogue)
    #     assert False, f"Unsupported Catalogue Request: {catalogue}"
