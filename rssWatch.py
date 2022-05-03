from setting import settings, log_warning_pure, log_email
import feedparser


def rss_watch(website: dict):
    r = ""
    origin: list = website["content"]
    new = rss_read(website["rss"])
    if website["init"]:
        settings.update_content(website["url"], new)
        log_email(f"{website['url']} 已经添加到监视清单",subject=f"{website['name']}已经添加到监视清单")
        settings.init_website(website["url"])
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
        log_warning_pure(f"{website['url']}已更新")
        r += "\n"
    return r


def rss_read(url: str):
    raw = feedparser.parse(url)
    return [i.title for i in raw.entries]
