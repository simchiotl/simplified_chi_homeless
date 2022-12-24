"""
Book requester
"""
import asyncio
import logging
import traceback

import aiohttp

from schomeless.schema import Chapter, Book
from schomeless.utils import Registerable

__all__ = [
    'BookRequester',
    'IterativeRequester',
    'AsyncRequester'
]

logger = logging.getLogger('Requester')


class BookRequester(metaclass=Registerable):
    def __init__(self, api):
        """

        Args:
            api (RequestApi):
        """
        self.api = api

    def run(self, book_properties=None, *args, **kwargs):
        """

        Args:
            book_properties (dict, optional): some constant attributes of ``Book``, e.g. preface.

        Returns:
            Book
        """
        book = Book(**book_properties)
        book.chapters = self.run_internal(*args, **kwargs)
        return book

    def run_internal(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Returns:
            List[Chapter]
        """
        raise NotImplementedError("``run_internal``")


class MultiPageRequester(BookRequester):
    """When there might be multiple page for one chapter"""

    def __init__(self, api, add_enter=False):
        super().__init__(api)
        self.add_enter = add_enter

    @staticmethod
    def reduce_page(chapter, page, add_enter=False):
        """

        Args:
            chapter (Chapter):
            page (Chapter):
            add_enter (bool, optional): whether add "\n" between content from different pages

        Returns:
            Chapter
        """
        if page is None:
            return chapter
        if chapter is None:
            chapter = Chapter(title=None, content='')
        if chapter.title is None:
            chapter.title = page.title
        else:
            assert chapter.title == page.title
        if add_enter:
            chapter.content += '\n'
        chapter.content += page.content
        return chapter


@BookRequester.register('ITER')
class IterativeRequester(MultiPageRequester):
    """Query book chapter by chapter"""

    def get_chapter(self, req):
        """

        Args:
            req (ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest)``
        """
        chapter = None
        try:
            while True:
                page, req = self.api.get_chapter(req)
                chapter = MultiPageRequester.reduce_page(chapter, page)
                if req is None or req.is_first:
                    break
        except Exception as e:
            traceback.print_exc()
        return chapter, req

    def run_internal(self, req):
        """

        Args:
            req (ChapterRequest)

        Returns:
            list[Chapter]
        """
        chapters = []
        while req is not None:
            chap, req = self.get_chapter(req)
            if chap is not None:
                chap.id = len(chapters)
                chapters.append(chap)
                logger.info(f"Chapter {chap.id + 1}: {chap.title}")
        return chapters


@BookRequester.register('ASYNC')
class AsyncRequester(MultiPageRequester):
    """Query book chapters asynchronously"""

    async def get_chapter(self, session, req, index):
        """

        Args:
            req (ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, ChapterRequest)``
        """
        try:
            page, next = await self.api.get_chapter_async(session, req)
            logger.info(f"Chapter {index + 1}: {page.title}")
            return True, dict(index=index, page=page, next=next)
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f'Error at {req}')
            return False, index, req

    def reduce(self, used, chapters, results):
        n_failed = 0
        for is_succ, result in results:
            if is_succ:
                index = result.pop('index')
                next = result.pop('next')
                chapters[index] = MultiPageRequester.reduce_page(chapters[index], result['page'], self.add_enter)
                if next is None or next.is_first:
                    used.pop(index)
                else:
                    used[index] = next
            else:
                n_failed += 1
        return n_failed

    async def core(self, reqs, *, headers=None):
        if headers is None:
            headers = {}
        tasks = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for i, req in reqs.items():
                tasks.append(asyncio.create_task(self.get_chapter(session, req, i)))
            return await asyncio.gather(*tasks)

    def run_internal(self, catalogue, *, retry_count=20, chapter_range=None, headers=None):
        """

        Args:
            catalogue (CatalogueRequest):
            retry_count (int):
            chapter_range (list[int], optional): id starts from 0
            headers (dict, optional):

        Returns:
            list[Chapter]
        """
        reqs = self.api.get_chapter_list(catalogue)
        n = len(reqs)
        if chapter_range is None:
            chapter_range = range(n)
        chapter_range = set(chapter_range)
        reqs = [r for i, r in enumerate(reqs) if i in chapter_range]

        retry = 0
        total = len(reqs)
        chapters = [Chapter(id=i) for i in range(total)]
        used = dict(enumerate(reqs))

        if headers is None:
            headers = {}
            headers['User-Agent'] = 'python-requests/2.27.1'
            headers['Connection'] = 'keep-alive'

        last_failed = None
        while retry < retry_count:
            results = asyncio.run(self.core(used, headers=headers))
            n_failed = self.reduce(used, chapters, results)
            logger.info(f"{total - len(used)}/{total} completed, {n_failed}/{total} failed"
                        f", {len(used) - n_failed}/{total} undergoing")
            if len(used) == 0:
                break
            if last_failed is not None and n_failed > 0 and last_failed == n_failed:
                retry += 1
            last_failed = n_failed

        return chapters
