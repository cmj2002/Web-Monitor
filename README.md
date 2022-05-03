# Web Monitor

监视网站更改并通过邮件通知，支持通过邮件订阅和取消订阅。

## 数据库配置

使用前需要先在服务器上安装并配置[MongoDB](https://www.mongodb.com/zh-cn) 。

### 建立数据库

安装好 [MongoDB](https://www.mongodb.com/zh-cn) 后，可以直接用 [MongoDB Compass](https://www.mongodb.com/zh-cn/products/compass) 管理数据库，连接方式非常简单，在后者的连接处输入 `mongodb://8.8.8.8:27017/` 即可（将 `8.8.8.8` 更改为你的服务器的公网IP，记得在安全组中开放端口 `27017` ）

为了数据库的安全性，通常会为数据库建立账户并将数据库改为只能通过账户访问。具体方式请 STFW 。

首先建立一个数据库，建议用项目的名字命名，比如 `example` 。

我把用户列表、监视网站列表、基本配置放进了数据库，因此在 `example` 下创建以下 `Collection`：

- `websites`，监视网站列表，包括其名称、URL、读取类型（后面会提到）、内容（程序保存以便下次比较的网页数据）。如果是网盘链接，还要存储密码。每个网站一行（MongoDB中称 `Document` ）。
- `users`，用户列表，仅包括用户邮箱。每个用户一行。
- `config`，程序配置，包括发件和收件邮箱、程序运行的周期大小等。整个 `Collection` 只有一行。

### websites

支持的网站分为五种 `type`：`common`，`ntlm`，`single_line`（通常不使用），`njubox`，`rss`，分别有不同的配置方式

下面的例子中：

* `type`，`content` 不能改
* `url` 需要输入目标网站的URL
* `user` 和 `password` 需要输入对应的密码
* `init` 始终填 `false`，程序初始化之后会把它改成 `true`
* 不包括 `_id` 字段，这是 MongoDB 自带的，如果不了解不要更改或删除

`common` 类型，检测普通的HTML网页：

```json
{
  "url": "http://www.example.com/",
  "type": "common",
  "init": false,
  "content": "",
  "name": "example"
}
```

`ntlm` 类型，通过 `ntlm` 认证方式进行认证，检测普通的HTML网页：

```json
{
  "url": "http://www.example.com/",
  "name": "example",
  "init": false,
  "type": "ntlm",
  "user": "username",
  "password": "123456",
  "content": ""
}
```

`single_line` 类型，也检测HTML，用于应对某些网页转换成Markdown后只有一行的情况：

```json
{
  "url": "http://www.example.com/",
  "name": "example",
  "type": "single_line",
  "init": false,
  "content": ""
}
```

`njubox` 类型，用于检测南京大学网盘分享链接（可能也可以检测基于 Seafile 的其他网盘分享链接，但是要自己改一下代码）：

```json
{
  "url": "https://box.nju.edu.cn/d/<token>/",
  "name": "example"
  "type": "njubox",
  "password": "123",
  "init": false,
  "content": ""
}
```

`rss` 类型，只检测文章标题更改：

```json
{
  "url": "http://www.example.com/",
  "name": "example"
  "type": "rss",
  "init": false,
  "content": [
    ""
  ]
}
```

> #### 可选配置
>
> `ntlm` 和 `common` 可以使用代理或者指定字符编码：
>
> * 代理配置，如 `"socks5": "127.0.0.1:1080"` ，指定 `socks5` 代理的位置。目前只支持 `socks5`。
> * 字符编码方式，如 `"charset": "utf-16"` ，指定使用 `utf-16` 解码网站内容。默认使用 `utf-8

### config

`config` 中只有一个行（MongoDB中称 `Document` ），示例中同样不包括 `_id` 字段。

除了 `sleep_time` 是 `Int32` 或 `Int64` 类型，其他都是 `String` 类型。

```json
{
    "notifier":"<用于发送提醒邮件的邮箱>",
    "notifierSMTP":"<用于发送提醒邮件的邮箱密码或授权码>",
    "cancel_receiver":"<用于取消订阅的邮箱>",
    "cancel_receiverIMAP":"<用于取消订阅的邮箱密码或授权码>",
    "subscribe_receiver":"<用于订阅的邮箱>",
    "subscribe_receiverIMAP":"<用于订阅的邮箱密码或授权码>",
    "support_email":"<提供给订阅者的支持邮箱>",
    "info_email":"<接受运行时信息的邮箱，包括新网站成功加入等>",
    "app_name":"<应用名称>",
    "sleep_time":<运行周期间隔，以秒为单位，Int32或Int64类型>,
}
```

### users

不用手动配置，它由程序管理

## 程序常量配置

运行本程序前，需要先对一些常量进行配置：

### 必选

```python
# setting.py
db_url = "mongodb://127.0.0.1:27017/" # 如果数据库不在本地，需要更改
db_name = "your_database_name" # 更改为你的数据库名
logging.basicConfig(level=logging.INFO) # 自定义log级别，不懂可以不改
smtp_host = 'smtp.qiye.aliyun.com' # 更改为你使用的smtp服务器
imap_host = 'imap.qiye.aliyun.com' # 更改为你使用的imap服务器
```

```python
# main.py
error_email="" # 当程序出现错误，会发送邮件到这个邮箱
```

### 可选

如果你使用的SMTP端口不是常用的 465，或者不使用SSL：

```python
# setting.py
def send_email(target: list, subject: str, content: str, sender: str, senderSMTP: str):
    c = myMdmail.EmailContent(content)
    smtp = {
        'host': smtp_host,
        'port': 465, # 更改端口
        'tls': False,
        'ssl': True, # 更改SSL
        'user': sender,
        'password': senderSMTP,
    }
    r = myMdmail.send(c, subject, from_email=sender, bcc=target, smtp=smtp)
    log_info_pure(f"邮件发送完成: {subject}，返回的字典为：\n{r}")
```

如果你使用的IMAP端口不是常用的 993，或者不使用SSL：

```python
# setting.py
class Setting:
    # ...
    def read_email(self, receiver, password, op_type):
        for i in range(10):
            try:
                email_server = imaplib.IMAP4_SSL(host=imap_host, port=993) # 更改这一行
            except Exception as e:
                if i < 9:
                    log_debug_pure(f"发生错误：{repr(e)}，进行第{i + 1}次尝试")
                else:
                    raise e
            else:
                break
        #...
```

## 更新日志

### v2.0

* 不再使用 `while` 实现持续运行，请自行使用 `crontab` 或类似功能设置定时任务
* 支持 `ntlm` 类型的认证
* 支持自定义的 `decode` 方式
* `ntlm` 和 `commonWatch` 支持通过代理进行请求（可以与 [Hagb/docker-easyconnect](https://github.com/Hagb/docker-easyconnect) 配合用于校园网内资源）
* 修复了一些问题

## Todo

* [ ] 重构为面向对象的结构
