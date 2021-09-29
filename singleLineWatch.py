import urllib.request

import html2text
from setting import settings, log_info_pure, log_email, log_debug_pure
import difflib


def single_line_watch(website: dict):
    """检测url是否发生变化，如果发生变化返回详细信息，否则返回空字符串。\n
    本函数逐行将HTML转换为Markdown，用于解决转换不标准的HTML时造成的换行异常问题，可能导致跨行组件转换异常。
    """
    new_text = single_line_read(website["url"])
    origin_text = website["content"]
    if origin_text == "":
        log_email(f"{website['url']} 已经添加到监视清单", subject=f"{website['name']}已经添加到监视清单")
        settings.update_content(website["url"], new_text)
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
        log_info_pure(f"{website['url']}已更新")
        return result


def single_line_read(url: str):
    """逐行将HTML转换为Markdown。
    用于解决转换不标准的HTML时造成的换行异常问题，可能导致跨行组件转换异常"""
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
    h.ignore_links = True
    h.protect_links = True
    h.ignore_emphasis = True
    h.body_width = 0
    h.single_line_break = True
    h.ignore_images = True
    output = ""
    for line in data.split('\n'):
        buf = h.handle(line)
        output += buf
    output = "".join([s for s in output.splitlines(True) if s.strip()])
    return output
