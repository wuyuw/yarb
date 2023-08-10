from rich import print
from rich.console import Console
from rich.progress import Progress
import jinja2
import requests
import json
import re

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


def google_translate(text, target='zh-CN', proxies=None):
    """
    google翻译
    :param text: 字符串
    :params target: 目标语言
    :params proxies: 代理
    :return: (result, bool)
    """
    base_url = f'http://translate.google.com/translate_a/single'
    params = {
        'client': 'at',
        'sl': 'en',
        'tl': target,
        'dt': 't',
        'q': text
    }
    res = requests.get(base_url, params=params, proxies=proxies)
    if not res.ok:
        return text, False
    try:
        return json.loads(res.text)[0][0][0], True
    except:
        return text, False
