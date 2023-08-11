from rich import print
from rich.console import Console
from rich.progress import Progress
import jinja2
import requests
import json
import re
import time
import threading
import random
from hashlib import md5


console = Console()
progress = Progress()


class Pattern:
    @staticmethod
    def create(length: int = 8192):
        pattern = ''
        parts = ['A', 'a', '0']
        while len(pattern) != length:
            pattern += parts[len(pattern) % 3]
            if len(pattern) % 3 == 0:
                parts[2] = chr(ord(parts[2]) + 1)
                if parts[2] > '9':
                    parts[2] = '0'
                    parts[1] = chr(ord(parts[1]) + 1)
                    if parts[1] > 'z':
                        parts[1] = 'a'
                        parts[0] = chr(ord(parts[0]) + 1)
                        if parts[0] > 'Z':
                            parts[0] = 'A'
        return pattern

    @staticmethod
    def offset(value: str, length: int = 8192):
        return Pattern.create(length).index(value)


def render_template(template, package="", **kwargs):
    """
    jinja2模板渲染
    """
    env = jinja2.Environment(loader=jinja2.PackageLoader("templates", package))
    tmpl = env.get_template(template)
    return tmpl.render(**kwargs)


def is_contain_chinese(word):
    """
    判断字符串是否包含中文字符
    :param word: 字符串
    :return: 布尔值,True表示包含中文,False表示不包含中文
    """
    pattern = re.compile(r'[\u4e00-\u9fa5]')
    match = pattern.search(word)
    return True if match else False


class GoogleTranslator(object):
    """谷歌翻译"""

    def __init__(self, base_url='http://translate.google.com/translate_a/single', proxy=None) -> None:
        self.base_url = base_url
        self.proxy = {'http': proxy, 'https': proxy} if proxy else None
        self._lock = threading.Lock()

    def translate(self, text, target='zh-CN'):
        params = {
            'client': 'at',
            'sl': 'en',
            'tl': target,
            'dt': 't',
            'q': text
        }
        error = ""

        for _ in range(5):
            with self._lock:
                res = requests.get(self.base_url, params=params,
                                   proxies=self.proxy)
            error = res.reason
            if res.status_code == 429:
                time.sleep(random.random())
                continue
            if not res.ok:
                return res.reason, False
            json_data = res.json()
            try:
                return json_data[0][0][0], True
            except Exception as e:
                return str(e), False
        return error, False


class BaiduTranslator(object):
    """百度翻译"""

    BASE_URL = 'http://api.fanyi.baidu.com/api/trans/vip/translate'

    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.limited = False

    @staticmethod
    def is_chinese(word):
        """
        检查整个字符串是否包含中文
        :param word: 需要检查的字符串
        :return: bool
        """
        for ch in word:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    @staticmethod
    def gen_salt():
        return str(int(time.time()))[-5:] + str(random.randint(10000, 99999))

    def get_sign(self, q, salt):
        """
        生成签名
        :param q: 查询字符串
        :param salt: 随机码
        :return: sign
        """
        s = self.app_id + q + salt + self.app_secret
        m = md5()
        m.update(s.encode())
        return m.hexdigest()

    def fanyi(self, text, retry=10):
        if self.limited:
            return "翻译额度不足", False
        salt = self.gen_salt()
        sign = self.get_sign(q=text, salt=salt)
        params = {
            'q': text,
            'from': 'en',
            'to': 'zh',
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        err_msg = ""
        for _ in range(retry):
            resp = requests.get(url=self.BASE_URL, params=params)
            err_msg = resp.text
            if not resp.ok:
                return err_msg, False
            json_data = resp.json()
            error_code = json_data.get('error_code')
            if error_code == '54004':
                self.limited = True
                return err_msg, False
            if error_code == '54003':
                time.sleep(random.random()*5)
                continue
            trans_result = json_data.get('trans_result')
            if not trans_result:
                return err_msg, False
            return trans_result[0].get('dst'), True
        return err_msg, False


if __name__ == '__main__':
    gt = GoogleTranslator(proxy='http://127.0.0.1:51837')
    res, ok = gt.translate("how are you?")
    print(res, ok)
