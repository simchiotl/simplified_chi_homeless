import os.path
from collections import defaultdict
from functools import reduce

from schomeless.api import UrlChapterRequest, OtherApi
from schomeless.schema import Chapter
from schomeless.utils import RequestsTool

__all__ = [
    'FeiazwApi',
    'ZwwxApi',
    'ShudaiziwxApi'
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


class ShudaiziwxApi(OtherApi):

    @staticmethod
    def clean_title(t):
        return t.split('章', maxsplit=1)[-1].strip()

    def get_chapter_internal(self, req, d):
        t = d('#content>h1').text()
        ct = d('#content .content').text()
        chap = Chapter(ShudaiziwxApi.clean_title(t), ct)
        return chap

    def get_next(self, req, d):
        host = RequestsTool.get_host(req.url)
        item = d('footer a.float-right')
        category = d('footer a.float-left:last')
        assert item.text().strip() == '下一页'
        href = item.attr('href')
        if href != category.attr('href'):
            return UrlChapterRequest(True, host + href)
        return None

    def get_chapter_list_internal(self, req, d):
        host = RequestsTool.get_host(req.url)
        reqs = defaultdict(list)
        req_list = []
        for item in d('.booklist li.list-group-item a'):
            url = host + item.attrib['href']
            req = UrlChapterRequest(True, url, ShudaiziwxApi.clean_title(item.text))
            reqs[req.title].append(len(req_list))
            req_list.append(req)
        # redundant = {k: v for k, v in reqs.items() if len(v) > 1}
        removed = reduce(lambda prev, curr: prev | set(curr[:-1]), reqs.values(), set())
        return [req for i, req in enumerate(req_list) if i not in removed]
