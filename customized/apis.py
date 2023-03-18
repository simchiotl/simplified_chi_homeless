import os.path

from schomeless.api import UrlChapterRequest, OtherApi
from schomeless.schema import Chapter, Book
from schomeless.utils import RequestsTool

__all__ = [
    'FeiazwApi',
    'ZwwxApi',
    'Wx75Api'
]

BASE_DIR = os.path.dirname(__file__)


class FeiazwApi(OtherApi):
    @staticmethod
    def clean_title(t):
        return t.split('章')[-1]

    def get_chapter_internal(self, req, d):
        t = d('.chaptertitle:first').text()
        ct = d('#content').text()
        is_noise = lambda l: '飞速中文' in l or 'feiazw' in l
        lines = ct.split('\n')
        while lines and is_noise(lines[0]):
            lines.pop(0)
        while lines and is_noise(lines[-1]):
            lines.pop()
        chap = Chapter(FeiazwApi.clean_title(t), '\n'.join(lines), int(t.split('.')[0]) - 1)
        return chap

    def get_next(self, req, d):
        host = RequestsTool.get_dirname(req.url)
        filename = d('#next').attr('href')
        nreq = UrlChapterRequest(True, os.path.join(host, filename))
        return nreq

    def get_chapter_list_internal(self, req, d):
        host = RequestsTool.get_dirname(req.url)
        reqs = []
        for item in d('.chapterlist:first a'):
            url = os.path.join(host, item.attrib['href'])
            reqs.append(UrlChapterRequest(True, url, FeiazwApi.clean_title(item.text)))
        return reqs


class ZwwxApi(OtherApi):

    def __init__(self, spliter):
        super().__init__()
        self.spliter = spliter

    @staticmethod
    def clean_title(t):
        return t.split('章')[-1].strip()

    def get_chapter_internal(self, req, d):
        t = d('.bookname:first h1').text()
        ct = d('#content').text()
        content = ct.split(self.spliter)[0]
        chap = Chapter(ZwwxApi.clean_title(t), content)
        return chap

    def get_next(self, req, d):
        host = RequestsTool.get_host(req.url)
        item = d('div.bottem2 a')[-2]
        assert item.text.strip() == '下一章'
        nurl = host + item.attrib['href']
        if nurl.endswith('html'):
            return UrlChapterRequest(True, nurl)
        return None

    def get_chapter_list_internal(self, req, d):
        host = RequestsTool.get_host(req.url)
        reqs = []
        for item in d('#list dd a'):
            url = host + item.attrib['href']
            reqs.append(UrlChapterRequest(True, url, ZwwxApi.clean_title(item.text)))
        return reqs


class Wx75Api(OtherApi):
    @staticmethod
    def clean_book(source, target, name='', author=''):
        with open(source, 'r') as fobj:
            text = fobj.read()
            first, second = text.split("""-------------可爱的分割线---------------
正文开始，更多好文请访问 75zw.com 
-------------可爱的分割线---------------""", maxsplit=1)
            lines = second.strip().split('\n')
            chapters = []
            title, content = None, []
            for line in lines:
                cline = line.strip()
                if cline.endswith('75zw.com'):
                    if title is not None or len(content) > 0:
                        chapters.append(Chapter(title, '\n'.join(content).strip()))
                    title = cline.split(' ', maxsplit=1)[0]
                    content = []
                elif title is not None:
                    content.append(cline)
            preface = "\n".join(first.strip().split('\n')[3:])
            book = Book(name=name, author=author, preface=preface, chapters=chapters)
            book.to_txt(target)
