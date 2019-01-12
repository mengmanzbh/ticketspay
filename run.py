# -*- coding=utf-8 -*-
from config.emailConf import sendEmail
from init import select_ticket_info
from init import pay_order


def run():
    # select_ticket_info.select().main()
    pay_order.payorder().main()



def Email():
    sendEmail(u"订票小助手测试一下")


if __name__ == '__main__':
    run()
    # Email()