import json
import logging
import os.path
import sys
from dataclasses import dataclass
from shutil import rmtree
from urllib.parse import urlparse, quote, parse_qs

import requests
from lxml import html
from pyquery import PyQuery as pq

__all__ = [
    'LogTool',
    'RequestsTool',
    'FileSysTool',
]


class LogTool:
    @staticmethod
    def confirm(message, silence=False):
        if silence:
            return True
        word = input(f"{message} (Type any char to stop):")
        return word.strip() == ''

    @staticmethod
    def get_log_level_code(level):
        """Get the integer for the given logging level"""
        level = level.upper()
        if level == 'NEVER':
            return logging.CRITICAL + 10
        return eval('logging.%s' % level)

    @staticmethod
    def config_logger(log_level='INFO'):
        """Configure logging level and log format

        Args:
            log_level (str or int): {``"NOTSET"`` | ``"DEBUG"`` | ``"INFO"`` | ``"WARNING"`` | ``"ERROR"`` | \
                                    ``"CRITICAL"`` | ``NEVER``}
        """
        FORMAT = "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
        DATE_FMT = "%H:%M:%S %Y-%m-%d"
        if isinstance(log_level, str):
            log_level = LogTool.get_log_level_code(log_level)
        kwargs = dict(format=FORMAT, datefmt=DATE_FMT, level=log_level)
        logging.basicConfig(**kwargs)


class RequestsTool:
    @staticmethod
    def quote(url, encoding='utf-8'):
        words = url.split('?', maxsplit=1)
        if len(words) == 1:
            return url
        url, query = words
        args = query.split('&')
        qargs = [f'{quote(k, encoding=encoding)}={quote(v, encoding=encoding)}' for k, v in
                 map(lambda x: x.split('='), args)]
        return url + '?' + "&".join(qargs)

    @staticmethod
    def get_host(url):
        return '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(url))

    @staticmethod
    def get_dirname(url):
        base, _ = os.path.split(url)
        return base

    @staticmethod
    def request(url, *, encoding='utf-8', method='GET', request_kwargs=None):
        if request_kwargs is None:
            request_kwargs = {}
        res = requests.request(method, url, **request_kwargs)
        res.raise_for_status()
        if res.apparent_encoding.lower() != encoding.lower():
            print(f"Maybe should be `{res.apparent_encoding}` encoding. Used it.", file=sys.stderr)
            res.encoding = res.apparent_encoding
        else:
            res.encoding = encoding
        return res.text

    @staticmethod
    async def request_async(session, url, *, encoding='utf-8', method='GET', request_kwargs=None):
        async def try_encodings_async(res):
            try:
                return await res.text()
            except UnicodeDecodeError as e:
                try:
                    return await res.text(encoding=encoding)
                except UnicodeDecodeError as e:
                    return RequestsTool.request(url, encoding=encoding, method=method,
                                                request_kwargs=request_kwargs)
            raise e

        if request_kwargs is None:
            request_kwargs = {}
        async with session.request(method, url, **request_kwargs) as res:
            return await try_encodings_async(res)

    @staticmethod
    def request_and_pyquery(url, encoding='utf-8', method='GET', request_kwargs=None):
        res = RequestsTool.request(url, encoding=encoding, method=method, request_kwargs=request_kwargs)
        a = html.fromstring(res)
        d = pq(a)
        return d

    @staticmethod
    async def request_and_pyquery_async(session, url, encoding='utf-8', method='GET', request_kwargs=None):
        res = await RequestsTool.request_async(session, url, encoding=encoding, method=method,
                                               request_kwargs=request_kwargs)
        d = pq(res)
        return d

    @staticmethod
    def request_and_json(url, encoding='utf-8', method='GET', request_kwargs=None):
        res = RequestsTool.request(url, encoding=encoding, method=method, request_kwargs=request_kwargs)
        d = json.loads(res)
        return d

    @staticmethod
    async def request_and_json_async(session, url, encoding='utf-8', method='GET', request_kwargs=None):
        res = await RequestsTool.request_async(session, url, encoding=encoding, method=method,
                                               request_kwargs=request_kwargs)
        d = json.loads(res)
        return d

    @staticmethod
    def parse_query(url):
        parsed_url = urlparse(url)
        captured_value = parse_qs(parsed_url.query)
        return {k: v[0] for k, v in captured_value.items()}


class FileSysTool:
    @dataclass
    class File:
        dirname: str = ''
        filename: str = ''
        extension: str = ''

        @staticmethod
        def parse(filepath):
            dirname, file = os.path.split(filepath)
            filename, ext = os.path.splitext(file)
            return FileSysTool.File(dirname, filename, ext)

    @staticmethod
    def enable_path(path, is_filepath=True):
        """Given a path that need to be written, make sure the directory exists

        Args:
            path (str): could either be a file path or a directory path
            is_filepath (bool): indicates whether ``path`` is a file path
        """
        path = os.path.abspath(path)
        if is_filepath:
            path, _ = os.path.split(path)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def delete_path(path):
        """Delete whatever at the path if it exists. If it's a file, remove it and it's index file.
        If it's a directory, remove the whole directory.

        Args:
            path (str): the path
        """
        if os.path.exists(path):
            if os.path.isdir(path):
                rmtree(path)
            else:
                if os.path.exists(path):
                    os.remove(path)
