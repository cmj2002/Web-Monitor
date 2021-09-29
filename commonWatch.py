import difflib
import urllib.request
from urllib.error import HTTPError

import html2text
from setting import settings, log_info_pure, log_email, log_debug_pure


def common_read(url: str):
    """将标准HTML转换为Markdown"""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for i in range(10):
        try:
            url_data = urllib.request.urlopen(req)
        except Exception as e:
            if i < 9:
                log_debug_pure(f"发生错误：{repr(e)}，进行第{i + 2}次尝试")
            else:
                raise e
        else:
            break
    url_data = url_data.read()
    data = url_data.decode("utf-8", "ignore")
    h = html2text.HTML2Text()
    h.body_width = 0
    output = h.handle(data)
    output = "".join([s for s in output.splitlines(True) if s.strip()])
    return output


def common_watch(website: dict):
    new_text = common_read(website["url"])
    origin_text = website["content"]
    if origin_text == "":
        log_email(f"{website['url']} 已经添加到监视清单", subject=f"{website['name']}已经添加到监视清单")
        settings.update_content(website["url"], new_text)
        return ""
    elif new_text == origin_text:
        return ""
    else:
        r = difflib.unified_diff(origin_text.splitlines(), new_text.splitlines(), n=2, lineterm="")
        result = "这些内容发生更改：\n\n```diff\n" + \
                 "\n".join(r) + \
                 "\n```\n\n"
        settings.update_content(website["url"], new_text)
        log_info_pure(f"{website['url']}已更新")
        return result
