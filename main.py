from setting import settings, send_email, log_email, log_info_pure
from commonWatch import common_watch
from singleLineWatch import single_line_watch
from rssWatch import rss_watch
from njuBoxWatch import njubox_watch
from ntlmWatch import ntlm_watch

log_info_pure("program start.")
settings.user_operation()
change_list = []
for website in settings.websites:
    # 获取网站的更改
    if website["type"] == "common":
        change = common_watch(website)
    elif website["type"] == "single_line":
        change = single_line_watch(website)
    elif website["type"] == "rss":
        change = rss_watch(website)
    elif website["type"] == "njubox":
        change = njubox_watch(website)
    elif website["type"] == "ntlm":
        change = ntlm_watch(website)
    else:
        log_email(f'url `{website["url"]}` 的类型 `{website["type"]}` 非法', subject=f"网站类型非法")
        change = ""
    # 记录更改
    if change != "":
        change_list.append((website["name"], website["url"], change))
if len(change_list) == 1:
    subject = f"{change_list[0][0]}已更改"
    msg = f"{change_list[0][0]}({change_list[0][1]})已更改！\n\n" + change_list[0][2]
    footer = "这封邮件由机器人发出，请勿直接回复\n\n" + \
             "如果要退订本服务，您可以用当前邮箱发送任意邮件到 {cancel_email}\n\n" + \
             "如果需要帮助，请发送邮件到 {support_email} ，这个邮箱由人类管理"
    footer = footer.format(cancel_email=settings.cancel_receiver, support_email=settings.support_email)
    msg += footer
    send_email(
        target=[u["email"] for u in settings.users],
        subject=subject,
        content=msg,
        sender=settings.notifier,
        senderSMTP=settings.notifierSMTP
    )
elif len(change_list) > 1:
    subject = f"{len(change_list)}个网站已更改"
    names_changed = "、".join([i[0] for i in change_list])
    msg = "网站 " + names_changed + " 已经发生更改\n\n"
    for i in change_list:
        msg += f"# {i[0]}\n\n"
        msg += "网址：" + i[1] + "\n\n"
        msg += i[2]
    footer = "这封邮件由机器人发出，请勿直接回复\n\n" + \
             "如果要退订本服务，您可以用当前邮箱发送任意邮件到 {cancel_email}\n\n" + \
             "如果需要帮助，请发送邮件到 {support_email} ，这个邮箱由人类管理"
    footer = footer.format(cancel_email=settings.cancel_receiver, support_email=settings.support_email)
    msg += footer
    send_email(
        target=[u["email"] for u in settings.users],
        subject=subject,
        content=msg,
        sender=settings.notifier,
        senderSMTP=settings.notifierSMTP
    )
log_info_pure("program done.")
