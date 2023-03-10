import logging
from dataclasses import dataclass
from typing import List, Optional

from schomeless.utils import DataClassExtension

__all__ = [
    'Book',
    'Chapter',
    'ChapterRequest',
    'CatalogueRequest',
    'BookInfoRequest'
]

logger = logging.getLogger('SCHEMA')

MAYBE_ERROR_THRESHOLD = 500
"""少于500字的视作可能的缺章"""


@dataclass
class Chapter(DataClassExtension):
    title: Optional[str] = None
    content: str = ''
    id: Optional[int] = None

    @staticmethod
    def cleaned_content(text):
        lines = text.split('\n')
        lines = [l for l in lines if l]
        return '\n\n'.join(lines)

    def to_txt(self, file_path):
        """

        Args:
            file_path:
        """
        with open(file_path, 'w') as fobj:
            fobj.write(self.title + "\n\n")
            L = len(self.content)
            if L < MAYBE_ERROR_THRESHOLD:
                logger.warning(f"Maybe invalid chapter:\nTitle: {self.title}, Content: {self.content}")
            fobj.write(self.content.strip())


@dataclass
class Book(DataClassExtension):
    chapters: Optional[List[Chapter]] = None
    preface: str = ''
    name: str = ''
    author: str = ''
    start_chapter: int = 1

    def __post_init__(self):
        if self.chapters is None:
            self.chapters = []

    def to_txt(self, file_path, preface_format="【{book.author}】{book.name}\n\n{book.preface}"):
        """

        Args:
            file_path:
            start_chapter (int): ``chap_id = chap_id + start_chapter``
        """
        with open(file_path, 'w') as fobj:
            if self.preface:
                fobj.write(preface_format.format(book=self) + "\n\n")
            for chapter in self.chapters:
                title = f"第{self.start_chapter + chapter.id}章 {chapter.title}"
                L = len(chapter.content)
                if L < MAYBE_ERROR_THRESHOLD:
                    logger.warning(f"Maybe invalid chapter:\nTitle: {title}, Content: {chapter.content}")
                fobj.write(f"{title}\n\n")
                fobj.write(chapter.content.strip())
                fobj.write('\n\n\n')

    @staticmethod
    def read_txt(file_path, name='', author=''):
        book = Book(name=name, author=author)
        chapter = None
        with open(file_path, 'r') as fobj:
            for line in fobj:
                words = line.split(' ', maxsplit=1)
                if len(words) > 1 and words[0].startswith('第') and words[0].endswith('章') and words[0][
                                                                                                1:-1].isdigit():
                    if chapter:
                        chapter.title = chapter.title.strip()
                        chapter.content = chapter.content.strip()
                        book.chapters.append(chapter)
                    chapter = Chapter(words[1], id=int(words[0][1:-1].strip()))
                elif chapter:
                    chapter.content += line
                else:
                    book.preface += line
        if chapter.title:
            book.chapters.append(chapter)
        if len(book.chapters):
            book.start_chapter = book.chapters[0].id
            for chap in book.chapters:
                chap.id -= book.start_chapter
        return book

    @staticmethod
    def compare(book1, book2, print_detail=False):
        """

        Args:
            book1 (Book):
            book2 (Book):
            print_detail (bool, optional): whether to print the first different lines of the unequal chapters.
        """

        def pretty_print(arr):
            s, e = -1, -1
            ans = []
            for a in arr:
                if a == e + 1:
                    e = a
                else:
                    if s > 0:
                        ans.append(f'{s}-{e}' if s != e else str(s))
                    s, e = a, a
            ans.append(f'{s}-{e}' if s != e else str(s))
            return ans

        def parse_title(t):
            return t.split('（')[0].split(' ', maxsplit=1)[0]

        def parse_content(c):
            lines = c.split('\n')
            lines = [l.strip() for l in lines if l]
            return lines

        logger = logging.getLogger('Comparing')

        ch1, ch2 = book1.chapters, book2.chapters
        if len(ch1) != len(ch2):
            logger.warning(f"Unequal chapter count: {len(ch1)} vs {len(ch2)}")
        diff = []
        for i, (c1, c2) in enumerate(zip(ch1, ch2)):
            if parse_title(c1.title) != parse_title(c2.title):
                logger.warning(f"Unequal title: `{c1.title}` vs `{c2.title}`")
            for j, (l1, l2) in enumerate(zip(parse_content(c1.content), parse_content(c2.content))):
                if l1 != l2:
                    diff.append(i + 1)
                    if print_detail:
                        logger.info(f"【Book1】{l1}")
                        logger.info(f"【Book2】{l2}")
                    break
        logger.warning(f'Unequal chapters: {pretty_print(diff)}')
        return diff


@dataclass
class ChapterRequest(DataClassExtension):
    """Abstract class for Chapter Request Spec"""
    is_first: bool
    """If it's just part of the chapter, whether it's the first part."""


@dataclass
class CatalogueRequest(DataClassExtension):
    """Abstract class for Catalogue Request Spec"""


@dataclass
class BookInfoRequest(DataClassExtension):
    """Abstract class for Book information Request Spec"""
