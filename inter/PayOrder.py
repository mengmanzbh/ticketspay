# coding=utf-8


class payOrder:
    def __init__(self, session):
        self.session = session

    def reqPayorder(self):
        """
        请求抢票页面
        :return:
        """
        pay_order_url = self.session.urls["payOrder"]
        pay_order_url_result = self.session.httpClint.send(pay_order_url, )
        print("*******OKOKOKOKOK*******")
        print(pay_order_url_result)
        return {
            "status": True
        }