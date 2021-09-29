import pymongo
import imaplib
import email
import time
import markdown.util
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging
import myMdmail

db_url = "mongodb://127.0.0.1:27017/"
logging.basicConfig(level=logging.INFO)
smtp_host = 'smtp.qiye.aliyun.com'
imap_host = 'imap.qiye.aliyun.com'


def send_email(target: list, subject: str, content: str, sender: str, senderSMTP: str):
    c = myMdmail.EmailContent(content)
    smtp = {
        'host': smtp_host,
        'port': 465,
        'tls': False,
        'ssl': True,
        'user': sender,
        'password': senderSMTP,
    }
    r = myMdmail.send(c, subject, from_email=sender, bcc=target, smtp=smtp)
    log_info_pure(f"邮件发送完成: {subject}，返回的字典为：\n{r}")


class Setting:
    def __init__(self):
        self.client = pymongo.MongoClient(db_url)
        self.db = self.client["20AI_course_reminder"]
        self.config_collection = self.db["config"]

        self.config = self.config_collection.find_one()
        self.notifier = self.config["notifier"]
        self.notifierSMTP = self.config["notifierSMTP"]
        self.subscribe_receiver = self.config["subscribe_receiver"]
        self.subscribe_receiverIMAP = self.config["subscribe_receiverIMAP"]
        self.cancel_receiver = self.config["cancel_receiver"]
        self.cancel_receiverIMAP = self.config["cancel_receiverIMAP"]
        self.support_email = self.config["support_email"]
        self.info_email = self.config["info_email"]
        self.app_name = self.config["app_name"]
        self.sleep_time = self.config["sleep_time"]

        self.websites = [i for i in self.db["websites"].find()]
        self.users = [i for i in self.db["users"].find()]

    def refresh(self):
        self.client = pymongo.MongoClient(db_url)
        self.db = self.client["20AI_course_reminder"]
        self.config_collection = self.db["config"]

        self.config = self.config_collection.find_one()
        self.notifier = self.config["notifier"]
        self.notifierSMTP = self.config["notifierSMTP"]
        self.subscribe_receiver = self.config["subscribe_receiver"]
        self.subscribe_receiverIMAP = self.config["subscribe_receiverIMAP"]
        self.cancel_receiver = self.config["cancel_receiver"]
        self.cancel_receiverIMAP = self.config["cancel_receiverIMAP"]
        self.support_email = self.config["support_email"]
        self.info_email = self.config["info_email"]
        self.app_name = self.config["app_name"]
        self.sleep_time = self.config["sleep_time"]

        self.websites = [i for i in self.db["websites"].find()]
        self.users = [i for i in self.db["users"].find()]

    def print_config(self):
        """just for debug"""
        print(
            self.notifier,
            self.notifierSMTP,
            self.subscribe_receiver,
            self.subscribe_receiverIMAP,
            self.cancel_receiver,
            self.cancel_receiverIMAP,
            self.support_email,
            sep='\n'
        )

    def push_mail_queue(self, target: str, subject: str, content: str, sender: str, senderSMTP: str):
        self.mail_queue.insert_one({
            "target": target,
            "subject": subject,
            "content": content,
            "sender": sender,
            "senderSMTP": senderSMTP
        })

    def add_user(self, user_email: str):
        if user_email in [u["email"] for u in self.users]:
            return False
        else:
            self.db["users"].insert_one({"email": user_email})
            self.refresh()
            return True

    def delete_user(self, user_email: str):
        if user_email in [u["email"] for u in self.users]:
            self.db["users"].delete_one({"email": user_email})
            self.refresh()
            return True
        else:
            return False

    def read_email(self, receiver, password, op_type):
        for i in range(10):
            try:
                email_server = imaplib.IMAP4_SSL(host=imap_host, port=993)
            except Exception as e:
                if i < 9:
                    log_debug_pure(f"发生错误：{repr(e)}，进行第{i + 1}次尝试")
                else:
                    raise e
            else:
                break
        email_server.login(user=receiver, password=password)
        email_server.select(mailbox='INBOX', readonly=False)
        status, data = email_server.search(None, 'UnSeen')
        email_list = data[0].split()
        r = []
        for email_id in email_list:
            email_type, row_email = email_server.fetch(email_id, '(RFC822)')
            msg = email.message_from_bytes(row_email[0][1])
            t = msg.get("Date")
            r.append((op_type, email.utils.parseaddr(msg.get('from'))[1],
                      time.strptime(msg.get("Date")[0:31],
                                    "%a, %d %b %Y %H:%M:%S %z")))  # 'Sun, 26 Sep 2021 18:22:56 +0800 (GMT+08:00)'
            email_server.store(email_id, '+FLAGS', r'(\Seen)')
        email_server.logout()
        return r

    def user_operation(self):
        self.refresh()
        operations = []
        operations.extend(self.read_email(self.subscribe_receiver, self.subscribe_receiverIMAP, "add"))
        operations.extend(self.read_email(self.cancel_receiver, self.cancel_receiverIMAP, "delete"))
        operations.sort(key=lambda x: x[2])
        add = []
        delete = []
        for op, user, t in operations:
            if op == "add":
                r = self.add_user(user)
                if r:
                    add.append(user)
            if op == "delete":
                r = self.delete_user(user)
                if r:
                    delete.append(user)
        if len(add) > 0:
            msg = "感谢您的订阅！建议您将 {notifier} 加入联系人，以免发送的提醒被您的邮箱拦截或放入垃圾堆\n\n" + \
                  "这封邮件由机器人发出，请勿直接回复\n\n" + \
                  "如果要退订本服务，您可以用当前邮箱发送任意邮件到 {cancel_email}\n\n" + \
                  "如果需要帮助，请发送邮件到 {support_email} ，这个邮箱由人类管理"
            msg = msg.format(notifier=self.notifier, cancel_email=self.cancel_receiver,
                             support_email=self.support_email)
            send_email(add, "订阅成功", msg, self.subscribe_receiver, self.subscribe_receiverIMAP)
        if len(delete) > 0:
            msg = "您已经成功取消订阅！\n\n" + \
                  "这封邮件由机器人发出，请勿直接回复\n\n" + \
                  "如果要重新订阅本服务，您可以用当前邮箱发送任意邮件到 {subscribe_email}\n\n" + \
                  "如果需要帮助，请发送邮件到 {support_email} ，这个邮箱由人类管理"
            msg = msg.format(notifier=self.notifier, subscribe_email=self.subscribe_receiver,
                             support_email=self.support_email)
            send_email(delete, "您已成功取消订阅", msg, self.cancel_receiver, self.cancel_receiverIMAP)

    def update_content(self, url: str, content):
        self.db["websites"].update_one({"url": url}, {"$set": {"content": content}})


settings = Setting()


def log_info_pure(msg: str):
    logging.info(time.strftime("%m-%d %H:%M:%S", time.localtime()) + "  " + msg)


def log_debug_pure(msg: str):
    logging.debug(time.strftime("%m-%d %H:%M:%S", time.localtime()) + "  " + msg)


def log_email(msg: str, subject="运行时信息"):
    logging.info(time.strftime("%m-%d %H:%M:%S", time.localtime()) + "  " + msg)
    send_email(target=settings.info_email, subject=f"INFO: {subject}", content=msg, sender=settings.notifier,
               senderSMTP=settings.notifierSMTP)


def log_error(msg: str):
    logging.error(time.strftime("%m-%d %H:%M:%S", time.localtime()) + "  " + msg)
