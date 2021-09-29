import regex as re
import requests
import json

from requests.adapters import HTTPAdapter

from setting import settings, log_info_pure, log_email


def njubox_watch(website: dict):
    new_text = njubox_read(website["url"], website["password"])
    origin_text = website["content"]
    if origin_text == "":
        log_email(f"{website['url']} 已经添加到监视清单", subject=f"{website['name']}已经添加到监视清单")
        settings.update_content(website["url"], new_text)
        return ""
    if new_text == origin_text:
        return ""

    r = ""
    new_list = json.loads(new_text)["dirent_list"]
    origin_list = json.loads(origin_text)["dirent_list"]

    origin_names = []
    new_names = []
    for i in origin_list:
        if i["is_dir"]:
            origin_names.append((i["folder_name"], i["last_modified"]))
        else:
            origin_names.append((i["file_name"], i["last_modified"]))
    for i in new_list:
        if i["is_dir"]:
            new_names.append((i["folder_name"], i["last_modified"]))
        else:
            new_names.append((i["file_name"], i["last_modified"]))

    changed = []
    add = []
    for i in new_names:
        if not (i[0] in [k[0] for k in origin_names]):
            add.append(i)
        for j in origin_names:
            if (i[0] == j[0]) and (i[1] != j[1]):
                changed.append(i)

    delete = []
    for i in origin_names:
        if not (i[0] in [k[0] for k in new_names]):
            delete.append(i)

    if len(changed) > 0:
        r += "以下文件（文件夹）发生改变：\n\n"
        for i in changed:
            r += f"* {i[0]}  （最后更改时间：{i[1][0:10]} {i[1][11:19]}）\n"
        r += "\n"

    if len(add) > 0:
        r += "添加了以下文件（文件夹）：\n\n"
        for i in add:
            r += f"* {i[0]}  （添加时间：{i[1][0:10]} {i[1][11:19]}）\n"
        r += "\n"

    if len(delete) > 0:
        r += "删除了以下文件（文件夹）：\n\n"
        for i in delete:
            r += f"* {i[0]}  （删除前的最后更改时间：{i[1][0:10]} {i[1][11:19]}）\n"
        r += "\n"

    settings.update_content(website["url"], new_text)
    log_info_pure(f"{website['url']}已更新")
    return r


def njubox_read(url: str, password: str):
    reg0 = r"https://box.nju.edu.cn/d/(.*)/"
    pattern0 = re.compile(reg0)
    token = pattern0.findall(url)[0]
    api_url = f"https://box.nju.edu.cn/api/v2.1/share-links/{token}/dirents/?thumbnail_size=48&path=%2F"

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=10))
    s.mount('https://', HTTPAdapter(max_retries=10))
    my_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4'
    }

    r = s.get(url, headers=my_headers)
    reg = r'<input type="hidden" name="csrfmiddlewaretoken" value="(.*)">'
    pattern = re.compile(reg)
    csrfmiddlewaretoken = pattern.findall(r.content.decode('utf-8'))[0]

    my_data = {
        'csrfmiddlewaretoken': csrfmiddlewaretoken,
        'token': token,
        "password": password
    }
    # 登录后
    my_headers = {
        'Host': 'box.nju.edu.cn',
        'Connection': 'keep-alive',
        'Content-Length': '125',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://box.nju.edu.cn',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': url,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    r = s.post(url, headers=my_headers,
               data=my_data)
    r = s.get(api_url)
    return r.text
