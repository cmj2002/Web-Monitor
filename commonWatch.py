import difflib
import requests

import html2text
from requests.adapters import HTTPAdapter

from setting import settings, log_warning_pure, log_email


def common_read(url: str, charset="utf-8", proxies=None):
    """将标准HTML转换为Markdown"""
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=10))
    s.mount('https://', HTTPAdapter(max_retries=10))
    response = s.get(url, proxies=proxies)
    url_data = response.content
    data = url_data.decode(charset, "ignore")
    h = html2text.HTML2Text()
    h.body_width = 0
    output = h.handle(data)
    output = "".join([s for s in output.splitlines(True) if s.strip()])
    return output


def common_watch(website: dict):
    # set proxy
    try:
        proxy = website["socks5"]
        proxies = {
            "http": "socks5://" + proxy,
            "https": "socks5://" + proxy
        }
    except KeyError:
        proxies = None

    # set charset
    try:
        charset = website["charset"]
    except KeyError:
        charset = "utf-8"

    new_text = common_read(website["url"], charset, proxies)
    origin_text = website["content"]
    if website["init"]:
        log_email(f"{website['url']} 已经添加到监视清单", subject=f"{website['name']}已经添加到监视清单")
        settings.update_content(website["url"], new_text)
        settings.init_website(website["url"])
        return ""
    elif new_text == origin_text:
        return ""
    else:
        """result = ""
        s = difflib.SequenceMatcher(None, origin_text, new_text)
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag == "insert":
                result += "新增这些内容：\n\n" + \
                          '\n> '.join(new_text[j1:j2].splitlines()) \
                          + "\n\n"
            elif tag == "replace":
                result += "这些内容被替换：\n\n原内容：\n\n" + \
                          "\n> ".join(origin_text[i1:i2].splitlines()) + \
                          "\n\n被替换为\n\n" + \
                          '\n> '.join(new_text[j1:j2].splitlines()) \
                          + "\n\n"
        assert True"""
        r = difflib.unified_diff(origin_text.splitlines(), new_text.splitlines(), n=2, lineterm="")
        result = "这些内容发生更改：\n\n```diff\n" + \
                 "\n".join(r) + \
                 "\n```\n\n"
        settings.update_content(website["url"], new_text)
        log_warning_pure(f"{website['url']}已更新")
        return result
