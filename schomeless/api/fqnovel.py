import logging
import os.path
import traceback
from dataclasses import dataclass
from typing import Optional

from fake_useragent import UserAgent
from pyquery import PyQuery
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from schomeless.api.base import RequestApi, UrlCatalogueRequest, UrlChapterRequest, CookieManager, UrlBookInfoRequest
from schomeless.schema import Chapter, ChapterRequest, CatalogueRequest, BookInfoRequest, Book
from schomeless.utils import RequestsTool

__all__ = [
    'FqNovelApi',
    'add_fqnovel_cookies',
]

BASE_DIR = os.path.dirname(__file__)
logger = logging.getLogger('API')
namespace = 'FQNOVEL'
TAG_TO_ID = {
    "都市": 1,
    "都市生活": 2,
    "玄幻": 7,
    "科幻": 8,
    "悬疑": 10,
    "乡村": 11,
    "历史": 12,
    "体育": 15,
    "武侠": 16,
    "影视小说": 45,
    "文学小说": 47,
    "生活": 48,
    "成功励志": 56,
    "文化历史": 62,
    "赘婿": 25,
    "神医": 26,
    "战神": 27,
    "奶爸": 42,
    "学霸": 82,
    "天才": 90,
    "腹黑": 92,
    "扮猪吃虎": 93,
    "鉴宝": 17,
    "系统": 19,
    "神豪": 20,
    "种田": 23,
    "重生": 36,
    "穿越": 37,
    "二次元": 39,
    "海岛": 40,
    "娱乐圈": 43,
    "空间": 44,
    "推理": 61,
    "洪荒": 66,
    "三国": 67,
    "末世": 68,
    "直播": 69,
    "无限流": 70,
    "诸天万界": 71,
    "大唐": 73,
    "宠物": 74,
    "外卖": 75,
    "星际": 77,
    "美食": 78,
    "年代": 79,
    "剑道": 80,
    "盗墓": 81,
    "战争": 97,
    "灵异": 100,
    "都市修真": 124,
    "家庭": 125,
    "明朝": 126,
    "职场": 127,
    "都市日常": 261,
    "都市脑洞": 262,
    "都市种田": 263,
    "历史脑洞": 272,
    "历史古代": 273,
    "惊悚": 322,
    "奥特同人": 367,
    "火影": 368,
    "反派": 369,
    "海贼": 370,
    "神奇宝贝": 371,
    "网游": 372,
    "西游": 373,
    "漫威": 374,
    "特种兵": 375,
    "龙珠": 376,
    "大秦": 377,
    "女帝": 378,
    "求生": 379,
    "聊天群": 381,
    "穿书": 382,
    "九叔": 383,
    "无敌": 384,
    "校花": 385,
    "单女主": 389,
    "无女主": 391,
    "都市青春": 396,
    "架空": 452,
    "开局": 453,
    "综漫": 465,
    "钓鱼": 493,
    "囤物资": 494,
    "四合院": 495,
    "国运": 496,
    "武将": 497,
    "皇帝": 498,
    "断层": 500,
    "宋朝": 501,
    "宫廷侯爵": 502,
    "清朝": 503,
    "抗战谍战": 504,
    "破案": 505,
    "神探": 506,
    "谍战": 507,
    "电竞": 508,
    "游戏主播": 509,
    "东方玄幻": 511,
    "异世大陆": 512,
    "高武世界": 513,
    "灵气复苏": 514,
    "末日求生": 515,
    "都市异能": 516,
    "修仙": 517,
    "特工": 518,
    "大小姐": 519,
    "大佬": 520,
    "打脸": 522,
    "双重生": 524,
    "同人": 538,
    "悬疑脑洞": 539,
    "克苏鲁": 705,
    "衍生同人": 718,
    "游戏体育": 746,
    "悬疑灵异": 751,
    "搞笑轻松": 778,
    "官场": 788,
    "现代言情": 3,
    "古代言情": 5,
    "幻想言情": 32,
    "婚恋": 34,
    "萌宝": 28,
    "豪门总裁": 29,
    "宠妻": 30,
    "公主": 83,
    "皇后": 84,
    "王妃": 85,
    "女强": 86,
    "皇叔": 87,
    "嫡女": 88,
    "精灵": 89,
    "团宠": 94,
    "校园": 4,
    "快穿": 24,
    "兽世": 72,
    "清穿": 76,
    "虐文": 95,
    "甜宠": 96,
    "宫斗宅斗": 246,
    "医术": 247,
    "玄幻言情": 248,
    "古言脑洞": 253,
    "马甲": 266,
    "现言脑洞": 267,
    "现言复仇": 268,
    "双男主": 275,
    "病娇": 380,
    "青梅竹马": 387,
    "女扮男装": 388,
    "民国": 390,
    "无CP": 392,
    "可盐可甜": 454,
    "天作之合": 455,
    "情有独钟": 456,
    "虐渣": 457,
    "护短": 458,
    "古灵精怪": 459,
    "独宠": 460,
    "群穿": 461,
    "古穿今": 462,
    "今穿古": 463,
    "异世穿越": 464,
    "闪婚": 466,
    "隐婚": 467,
    "冰山": 468,
    "双面": 469,
    "替身": 470,
    "契约婚姻": 471,
    "豪门世家": 473,
    "日久生情": 474,
    "破镜重圆": 475,
    "双向奔赴": 476,
    "一见钟情": 477,
    "强强": 478,
    "带球跑": 479,
    "逃婚": 480,
    "暗恋": 482,
    "相爱相杀": 483,
    "HE": 484,
    "职场商战": 485,
    "明星": 486,
    "医生": 487,
    "律师": 488,
    "现言萌宝": 489,
    "厨娘": 490,
    "毒医": 491,
    "将军": 492,
    "作精": 521,
    "前世今生": 523,
    "逃荒": 557,
    "双洁": 702,
    "双女主": 704,
    "豪门爽文": 745,
    "悬疑恋爱": 747,
    "霸总": 748,
    "青春甜宠": 749,
    "职场婚恋": 750,
    "诗歌散文": 46,
    "社会科学": 50,
    "名著经典": 51,
    "科技": 52,
    "经济管理": 53,
    "教育": 54,
    "推理悬疑": 61,
    "中国名著": 98,
    "外国名著": 99,
    "国学": 116,
    "法律": 142,
    "两性": 274,
    "外国文学": 397,
    "古代文学": 398,
    "当代文学": 399,
    "现实小说": 400,
    "文学理论": 401,
    "中国历史": 402,
    "世界历史": 403,
    "历史传记": 404,
    "人文社科": 405,
    "哲学宗教": 406,
    "心理学": 407,
    "政治军事": 408,
    "人物传记": 409,
    "个人成长": 410,
    "思维智商": 411,
    "人际交往": 412,
    "文化艺术": 413,
    "亲子家教": 415,
    "保健养生": 416,
    "时尚美妆": 418,
    "美食休闲": 419,
    "家居旅游": 420,
    "风水占卜": 421,
    "经典国学": 423,
    "学校教育": 721,
    "成人教育": 722
}
ID_TO_TAG = {v: k for k, v in TAG_TO_ID.items()}
UA = UserAgent(os='android')


class TextEncoder:
    CODE_START = 58344
    CHARSET = [
        'D', '在', '主', '特', '家', '军', '然', '表', '场', '4', '要', '只', 'v', '和', '?', '6', '别', '还', 'g',
        '现', '儿', '岁', '?', '?', '此', '象', '月', '3', '出', '战', '工', '相', 'o', '男', '直', '失', '世', 'F',
        '都', '平', '文', '什', 'V', 'O', '将', '真', 'T', '那', '当', '?', '会', '立', '些', 'u', '是', '十', '张',
        '学', '气', '大', '爱', '两', '命', '全', '后', '东', '性', '通', '被', '1', '它', '乐', '接', '而', '感', '车',
        '山', '公', '了', '常', '以', '何', '可', '话', '先', 'p', 'i', '叫', '轻', 'M', '士', 'w', '着', '变', '尔',
        '快', 'l', '个', '说', '少', '色', '里', '安', '花', '远', '7', '难', '师', '放', 't', '报', '认', '面', '道',
        'S', '?', '克', '地', '度', 'I', '好', '机', 'U', '民', '写', '把', '万', '同', '水', '新', '没', '书', '电',
        '吃', '像', '斯', '5', '为', 'y', '白', '几', '日', '教', '看', '但', '第', '加', '候', '作', '上', '拉', '住',
        '有', '法', 'r', '事', '应', '位', '利', '你', '声', '身', '国', '问', '马', '女', '他', 'Y', '比', '父', 'x',
        'A', 'H', 'N', 's', 'X', '边', '美', '对', '所', '金', '活', '回', '意', '到', 'z', '从', 'j', '知', '又', '内',
        '因', '点', 'Q', '三', '定', '8', 'R', 'b', '正', '或', '夫', '向', '德', '听', '更', '?', '得', '告', '并',
        '本', 'q', '过', '记', 'L', '让', '打', 'f', '人', '就', '者', '去', '原', '满', '体', '做', '经', 'K', '走',
        '如', '孩', 'c', 'G', '给', '使', '物', '?', '最', '笑', '部', '?', '员', '等', '受', 'k', '行', '一', '条',
        '果', '动', '光', '门', '头', '见', '往', '自', '解', '成', '处', '天', '能', '于', '名', '其', '发', '总',
        '母', '的', '死', '手', '入', '路', '进', '心', '来', 'h', '时', '力', '多', '开', '已', '许', 'd', '至', '由',
        '很', '界', 'n', '小', '与', 'Z', '想', '代', '么', '分', '生', '口', '再', '妈', '望', '次', '西', '风', '种',
        '带', 'J', '?', '实', '情', '才', '这', '?', 'E', '我', '神', '格', '长', '觉', '间', '年', '眼', '无', '不',
        '亲', '关', '结', '0', '友', '信', '下', '却', '重', '己', '老', '2', '音', '字', 'm', '呢', '明', '之', '前',
        '高', 'P', 'B', '目', '太', 'e', '9', '起', '稜', '她', '也', 'W', '用', '方', '子', '英', '每', '理', '便',
        '四', '数', '期', '中', 'C', '外', '样', 'a', '海', '们', '任'
    ]

    @classmethod
    def _interpret(cls, char):
        code = ord(char)
        bias = code - cls.CODE_START
        if bias < 0 or bias >= len(cls.CHARSET) or cls.CHARSET[bias] == '?':
            return char
        return cls.CHARSET[bias]

    @classmethod
    def decrypt(cls, text):
        try:
            return "".join(map(cls._interpret, text))
        except Exception as e:
            logger.warning(traceback.format_exc())


@CookieManager.register(namespace.lower())
def add_fqnovel_cookies(cookie=None):
    """

    Args:
        cookie (str, optional): cookie string like ``"key=name;key2=name2"``. If provided, use it. \
                                Otherwise, get new cookie by re-login.
    """

    def token_exist(browser):
        cookies = browser.get_cookies()
        return any(a['name'].startswith('Hm_lpvt') for a in cookies)

    info = CookieManager.load_info(namespace.lower())
    if cookie is None:
        browser = webdriver.Chrome()
        browser.get('https://fanqienovel.com/')
        browser.find_element(value='user-login', by=By.CLASS_NAME).find_element(value='a', by=By.TAG_NAME).click()
        browser.find_element(value='form-title-normal', by=By.CLASS_NAME).click()
        browser.find_element(value='username', by=By.NAME).send_keys(info.get('name', ''))
        browser.find_element(value='password', by=By.NAME).send_keys(info.get('password', ''))
        browser.find_element(value='sso_submit').click()
        WebDriverWait(browser, timeout=300).until(token_exist)
        cookie = ';'.join(f"{a['name']}={a['value']}" for a in browser.get_cookies())
        browser.quit()
        logger.info('Login succeeded.')
    return cookie


@RequestApi.register(namespace)
class FqNovelApi(RequestApi):
    """
    Use the xposed module and start the web service to get the chapter content

    When using the emulator from Android Studio:
    * open web server on FQWeb app on the emulator
    * make sure ``adb`` is installed and forward the port to local machine.

    References:
        * xposed module: https://github.com/fengyuecanzhu/FQWeb/tree/master
        * web service: https://telegra.ph/FQWeb-07-18
        * port forwarding: https://developer.android.com/tools/adb#forwardports
    """
    CATALOGUE_WEB_API = "https://fanqienovel.com/page/{req.book_id}"
    CATALOGUE_APP_API = "https://novel.snssdk.com/api/novel/book/directory/list/v1/"
    CHAPTER_WEB_API = f"https://fanqienovel.com/api/reader/full"
    CHAPTER_APP_API = f"https://fqnovel.pages.dev/content"
    SEARCH_APP_API = 'http://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/'
    ENCODING = 'utf-8'

    @dataclass
    class ChapterRequest(ChapterRequest):
        item_id: int
        title: Optional[str] = None

    @dataclass
    class CatalogueRequest(CatalogueRequest):
        book_id: int

        @staticmethod
        def search_for(keywords, take=0):
            params = {
                'aid': 13,
                'q': keywords,
                'offset': (take // 10) * 10
            }
            idx = take % 10
            res = RequestsTool.request_and_json(
                FqNovelApi.SEARCH_APP_API,
                method='GET',
                encoding=FqNovelApi.ENCODING,
                request_kwargs=dict(params=params)
            )
            items = res['data']['ret_data']
            if len(items) <= idx:
                return None
            return FqNovelApi.CatalogueRequest(int(items[idx]['book_id']))

    @dataclass
    class BookInfoRequest(BookInfoRequest):
        book_id: int

    def __init__(self, web_service_port=9999):
        super().__init__()
        self.port = web_service_port
        self.cookies = CookieManager.get_cookie(namespace.lower())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Danger hiptop 3.4; U; AvantGo 3.2)",
            'cookie': self.cookies
        }

    # ====================== Get chapter ===========================
    @staticmethod
    def _parse_last_int(url, spliter):
        try:
            pure_url = url.split('?')[0]
            integer = int(pure_url.split(spliter)[-1])
            return integer
        except Exception as e:
            raise ValueError(f'The URL should be formatted as: `http*<spliter><integer>?*`')

    @staticmethod
    def _parse_title(raw):
        return raw.split('章', maxsplit=1)[-1].strip()

    @staticmethod
    def _parse_from_url_request(req):
        item_id = FqNovelApi._parse_last_int(req.url, 'reader/')
        return FqNovelApi.ChapterRequest(req.is_first, item_id, req.title)

    def _preprocess_chapter_web(self, req):
        return {
            'itemId': req.item_id,
        }

    @staticmethod
    def _parse_chapter_content(content):
        if "</p>" in content:
            content = PyQuery(content).text()
        content = "\n".join(map(str.strip, content.split('\n')))
        return TextEncoder.decrypt(content)

    @staticmethod
    def _parse_chapter_web(req, item):
        if int(item.get('code', '0')) != 0:
            return None, None
        data = item['data']['chapterData']
        next_item = data['nextItemId']
        title = FqNovelApi._parse_title(data['title'])
        content = FqNovelApi._parse_chapter_content(data['content'])
        next = FqNovelApi.ChapterRequest(req.is_first, int(next_item)) if next_item else None
        return Chapter(title, content), next

    def get_chapter_web(self, req):
        item = RequestsTool.request_and_json(
            FqNovelApi.CHAPTER_WEB_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_web(req))
        )
        return FqNovelApi._parse_chapter_web(req, item)

    def _preprocess_chapter_app(self, req):
        return {
            'item_id': req.item_id,
        }

    @staticmethod
    def _parse_chapter_app(req, item):
        chap = None
        if '内容获取失败' not in item:
            chap = Chapter(req.title, FqNovelApi._parse_chapter_content(item))
        return chap, None

    def get_chapter_app(self, req):
        item = RequestsTool.request(
            FqNovelApi.CHAPTER_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req))
        )
        return FqNovelApi._parse_chapter_app(req, item)

    def get_chapter(self, req):
        """

        Args:
            req (UrlChapterRequest, or FqNovelApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, FqNovelApi.ChapterRequest=None)``. If ``FqNovelApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = FqNovelApi._parse_from_url_request(req)
        try:
            chap_app, next_app = self.get_chapter_app(req)
        except Exception as e:
            chap_app, next_app = None, None
        chap_web, next_web = self.get_chapter_web(req)
        if chap_app is not None:
            chap_web.content = chap_app.content
        return chap_web, next_web

    async def get_chapter_web_async(self, session, req):
        item = await RequestsTool.request_and_json_async(
            session,
            FqNovelApi.CHAPTER_WEB_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_web(req)))
        return FqNovelApi._parse_chapter_web(req, item)

    async def get_chapter_app_async(self, session, req):
        item = await RequestsTool.request_async(
            session,
            FqNovelApi.CHAPTER_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers,
                                params=self._preprocess_chapter_app(req))
        )
        return FqNovelApi._parse_chapter_app(req, item)

    async def get_chapter_async(self, session, req):
        """

        Args:
            session (aiohttp.ClientSession):
            req (UrlChapterRequest, or FqNovelApi.ChapterRequest):

        Returns:
            2-tuple: ``(Chapter, FqNovelApi.ChapterRequest=None)``. If ``FqNovelApi.ChapterRequest`` is None, no next chapter.
        """
        if isinstance(req, UrlChapterRequest):
            req = FqNovelApi._parse_from_url_request(req)
        chap_app, next_app = await self.get_chapter_app_async(session, req)
        chap_web, next_web = await self.get_chapter_web_async(session, req)
        chap_web.content = chap_app.content
        return chap_web, next_web

    # ====================== Get chapter list ===========================
    @staticmethod
    def _get_chapter_list_params(req):
        return {
            'book_id': req.book_id,
            'device_platform': 'android',
            'version_code': 600,
            'novel_version': None,
            'app_name': 'news_article',
            'version_name': '6.0.0',
            'app_version': '6.0.0aid=520',
            'channel': '1',
            'device_type': 'landseer',
            'os_api': '25',
            'os_version': '10',
        }

    @staticmethod
    def _parse_from_url_catalogue_request(req):
        """

        Args:
            req (UrlCatalogueRequest):

        Returns:
            FqNovelApi.CatalogueRequest
        """
        try:
            return FqNovelApi.CatalogueRequest(book_id=FqNovelApi._parse_last_int(req.url, 'page/'))
        except Exception as e:
            raise ValueError(f'Invalid FQNOVEL catalogue URL: `{req.url}`')

    def get_chapter_list_web(self, req):
        def get_item(item):
            url = 'https://fanqienovel.com' + item.attrib.get('href')
            spec = FqNovelApi._parse_from_url_request(UrlChapterRequest(True, url))
            spec.title = FqNovelApi._parse_title(item.text.strip())
            return spec

        catalogue = FqNovelApi.CATALOGUE_WEB_API.format(req=req)
        d = RequestsTool.request_and_pyquery(catalogue, FqNovelApi.ENCODING,
                                             request_kwargs=dict(headers=self.headers))
        items = list(d("div.chapter-item a.chapter-item-title"))
        return list(map(get_item, items))

    def get_chapter_list_app(self, req):
        params = FqNovelApi._get_chapter_list_params(req)
        res = RequestsTool.request_and_json(
            FqNovelApi.CATALOGUE_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers, params=params))
        if int(res.get('code', '-1')) != 0:
            logger.warning("Failed to get book info.")
        items = res['data'].get('item_list', [])
        return [FqNovelApi.ChapterRequest(
            True,
            int(item)
        ) for item in items]

    def get_chapter_list(self, req):
        """

        Args:
            req (UrlCatalogueRequest, or FqNovelApi.CatalogueRequest):

        Returns:
            list[FqNovelApi.ChapterRequest]
        """
        if isinstance(req, UrlCatalogueRequest):
            req = FqNovelApi._parse_from_url_catalogue_request(req)
        try:
            chapters = self.get_chapter_list_app(req)
        except Exception as e:
            chapters = self.get_chapter_list_web(req)
        return chapters

    # ====================== Get Book Info ===========================
    def get_book_info(self, req):
        if isinstance(req, (UrlBookInfoRequest, UrlCatalogueRequest)):
            req = FqNovelApi.BookInfoRequest(FqNovelApi._parse_from_url_catalogue_request(req).book_id)
        params = FqNovelApi._get_chapter_list_params(req)
        res = RequestsTool.request_and_json(
            FqNovelApi.CATALOGUE_APP_API,
            encoding=FqNovelApi.ENCODING,
            request_kwargs=dict(headers=self.headers, params=params))
        if int(res.get('code', '-1')) != 0:
            logger.warning("Failed to get book info.")
        info = res['data']['book_info']
        tag_ids = list(map(lambda x: int(x.strip()), info['category_v2_ids'].split(',')))
        tags = ", ".join([ID_TO_TAG[t] for t in tag_ids if t in ID_TO_TAG])
        return Book(
            name=info['book_name'],
            author=info['author'],
            preface=f"{info['abstract']}\n\n{tags}"
        )


if __name__ == '__main__':
    print(TextEncoder.CODE_END - TextEncoder.CODE_START + 1)
    print(len(TextEncoder.CHARSET))
