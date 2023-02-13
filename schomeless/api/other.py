"""Other APIs. Maybe temporal."""

import logging
import os.path

from schomeless.api.base import RequestApi, UrlChapterRequest
from schomeless.utils import RequestsTool

__all__ = [
    'OtherApi'
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
temp_path = os.path.join(BASE_DIR, '../../temp/{filename}')


class OtherApi(RequestApi):
    encoding = 'utf-8'

    def get_chapter_internal(self, req, d):
        """Get the chapter content

        Args:
            req (ChapterRequest): the current request
            d (PyQuery): the parsed HTML node.

        Returns:
            Chapter
        """
        raise NotImplementedError("``get_chapter_internal``")

    def get_next(self, req, d):
        """Get next request

        Args:
            req (ChapterRequest): the current request
            d (PyQuery): the parsed HTML node.

        Returns:
            ChapterRequest
        """
        raise NotImplementedError("``get_next``")

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest): Could be a url like: ``https://www.feiazw.com/Html/20929/17287505.html``

        Returns:
            2-tuple: ``(Chapter, None)``. Don't support iterative request when using App's API
        """
        d = RequestsTool.request_and_pyquery(req.url)
        return self.get_chapter_internal(req, d), self.get_next(req, d)

    async def get_chapter_async(self, session, req):
        d = await RequestsTool.request_and_pyquery_async(session, req.url)
        return self.get_chapter_internal(req, d), self.get_next(req, d)

    def get_chapter_list_internal(self, req, d):
        """Get chapter requests

        Args:
            req (CatalogueRequest):
            d (PyQuery):

        Returns:
            List[ChapterRequest]:
        """
        raise NotImplementedError("``get_chapter_requests``")

    def get_chapter_list(self, catalog):
        d = RequestsTool.request_and_pyquery(catalog.url)
        return self.get_chapter_list_internal(catalog, d)
