import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlBookInfoRequest, CookieManager
from schomeless.schema import Chapter, Book, BookInfoRequest, CatalogueRequest, ChapterRequest
from schomeless.utils import RequestsTool

__all__ = [
    'Po18MirrorApi',
    'Po18Api'
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'PO18'


@CookieManager.register(namespace.lower())
def add_po18_cookies(cookie=None):
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
        browser.get('https://members.po18.tw/apps/login.php')
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


@RequestApi.register('PO18_MIRROR')
class Po18MirrorApi(RequestApi):
    BOOK_INFO_API = "https://www.po18x.vip/{req.prefix}/{req.book_id}/"
    TXT_API = "https://www.po18x.vip/txt/{req.book_id}/"
    BOOK_INFO_ENCODING = 'gbk'
    TXT_ENCODING = 'GB18030'

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

        def __post_init__(self):
            self.prefix = int(self.book_id / 1000)

    def __init__(self):
        super().__init__()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }

    # ====================== Get Book and Info ===========================
    @staticmethod
    def _url_to_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            Po18MirrorApi.CatalogueRequest
        """
        try:
            return Po18MirrorApi.BookInfoRequest(book_id=int(req.url.strip('/').split('/')[-1]))
        except Exception as e:
            raise ValueError(f'Invalid PO18-Mirror catalogue URL: `{req.url}`')

    def _parse_book(self, text):
        def append_chapter():
            if len(chapter) > 0 or title is not None:
                chapters.append(Chapter(title, '\n'.join(chapter)))

        lines = text.split('\n')
        chapters = []
        name, title, chapter = None, None, []
        for line in lines:
            cline = line.strip()
            if len(cline) > 0:
                if name is None:
                    name = cline[1:-1]
                else:
                    spaces = line.split(cline, maxsplit=1)[0]
                    if len(spaces) == 1:
                        # chapter title
                        # push last chapter
                        append_chapter()
                        chapter = []
                        title = cline
                    else:
                        chapter.append(cline)
            elif len(chapter) > 0:
                chapter.append(cline)
        append_chapter()
        return Book(chapters, name=name)

    def get_book_info(self, req):
        d = RequestsTool.request_and_pyquery(
            Po18MirrorApi.BOOK_INFO_API.format(req=req),
            Po18MirrorApi.BOOK_INFO_ENCODING,
            request_kwargs=dict(headers=self.headers)
        )
        divbox = d('div.divbox')
        title = divbox('h2.ratitle').text().strip()
        preface = divbox('div.gray').text().strip()
        author = divbox('div').text().split('作者：', maxsplit=1)[-1].split('　', maxsplit=1)[0]
        return Book(preface=preface, name=title, author=author)

    def get_book(self, req):
        """Get the book directly

        Args:
            req (BookInfoRequest):

        Returns:
            Book
        """
        if isinstance(req, UrlBookInfoRequest):
            req = Po18MirrorApi._url_to_request(req)
        text = RequestsTool.request(
            Po18MirrorApi.TXT_API.format(req=req),
            encoding=Po18MirrorApi.TXT_ENCODING,
            request_kwargs=dict(headers=self.headers),
        )
        content = self._parse_book(text)
        book = self.get_book_info(req)
        assert book.name == content.name
        book.chapters = content.chapters
        return book


@RequestApi.register(namespace)
class Po18Api(RequestApi):
    CATALOGUE_API = "https://www.po18.tw/books/{req.book_id}/articles"
    CONTENT_API = "https://www.po18.tw/books/{req.book_id}/articlescontent/{req.chapter_id}"
    CHAPTER_API = "https://www.po18.tw/books/{req.book_id}/articles/{req.chapter_id}"
    BOOK_INFO_API = "https://www.po18.tw/books/{req.book_id}"
    ENCODING = 'utf-8'

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        book_id: int

    @dataclass
    class ChapterRequest(ChapterRequest):
        book_id: int
        chapter_id: int
        title: Optional[str] = None

    def __init__(self):
        super().__init__()
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            'cookie': self.cookies
        }

    @staticmethod
    def _parse_last_id(url):
        return int(url.strip('/').split('/')[-1])

    # ====================== Get Chapter ===========================
    def _postprocess_chapter(self, req, d):
        title = d('h1').text().strip()
        content = "\n".join([item.text.strip() for item in d('p') if item.text is not None])
        if not title or not content:
            title = req.title
        return Chapter(title, content), None

    def get_chapter(self, req):
        headers = dict(**self.headers)
        headers.update({
            'referer': Po18Api.CHAPTER_API.format(req=req)
        })
        d = RequestsTool.request_and_pyquery(
            Po18Api.CONTENT_API.format(req=req),
            Po18Api.ENCODING,
            request_kwargs=dict(headers=headers)
        )
        return self._postprocess_chapter(req, d)

    async def get_chapter_async(self, session, req):
        headers = dict(**self.headers)
        headers.update({
            'referer': Po18Api.CHAPTER_API.format(req=req)
        })
        d = await RequestsTool.request_and_pyquery_async(
            session,
            Po18Api.CONTENT_API.format(req=req),
            Po18Api.ENCODING,
            request_kwargs=dict(headers=headers)
        )
        return self._postprocess_chapter(req, d)

    # ====================== Get Chapter List ===========================
    def get_chapter_list(self, req):
        """Get the chapter links

        Args:
            req (CatalogueRequest):

        Returns:
            list[ChapterRequest]
        """
        chapters = []
        pid = 1
        while True:
            d = RequestsTool.request_and_pyquery(
                Po18Api.CATALOGUE_API.format(req=req),
                Po18Api.ENCODING,
                request_kwargs=dict(headers=self.headers, params=dict(page=pid)),
            )
            items = d('div.c_l')
            n = len(items)
            for i in range(n):
                item = items.eq(i)
                title = item('div.l_chaptname').text().strip()
                link = item('div.l_btn a')
                href = link.attr('href')
                if href.startswith('javascript'):
                    chapter_id = int(link.attr('name').strip().split('pop_order', maxsplit=1)[-1])
                else:
                    chapter_id = Po18Api._parse_last_id(href)
                chapters.append(Po18Api.ChapterRequest(True, req.book_id, chapter_id, title))
            pid += 1
            has_next = any(item.text.strip() == '>' for item in d('#w1 a'))
            if not has_next:
                break
        return chapters

    # ====================== Get Book Info ==============================
    def get_book_info(self, req):
        d = RequestsTool.request_and_pyquery(
            Po18Api.BOOK_INFO_API.format(req=req),
            request_kwargs=dict(headers=self.headers)
        )
        name = d('h1.book_name').text().strip()
        author = d('a.book_author').text().strip()
        preface = d('div.B_I_content').text().strip()
        return Book(name=name, author=author, preface=preface)
