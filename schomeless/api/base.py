import os.path
from dataclasses import dataclass
from typing import Optional

from schomeless.schema import ChapterRequest, CatalogueRequest
from schomeless.utils import Registerable

__all__ = [
    'RequestApi',
    'UrlChapterRequest',
    'UrlCatalogueRequest'
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


@dataclass
class UrlChapterRequest(ChapterRequest):
    url: str
    title: Optional[str] = None


@dataclass
class UrlCatalogueRequest(CatalogueRequest):
    url: str
