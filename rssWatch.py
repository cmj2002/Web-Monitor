from setting import settings, log_info_pure, log_email
import feedparser


def rss_watch(website: dict):
    r = ""
    origin: list = website["content"]
    new = rss_read(website["url"])
    if len(origin) == 0:
        settings.update_content(website["url"], new)
        log_email(f"{website['url']} 已经添加到监视清单",subject=f"{website['name']}已经添加到监视清单")
        return ""
    for i in new:
        if i in origin:
            continue
        else:
            r += f"* 增加了题目 `{i}`\n"
    for j in origin:
        if j in new:
            continue
        else:
            r += f"* 删除了题目 `{j}`\n"
    if r != "":
        settings.update_content(website["url"], new)
        log_info_pure(f"{website['url']}已更新")
        r += "\n"
    return r


def rss_read(url: str):
    raw = feedparser.parse(url)
    return [i.title for i in raw.entries]
