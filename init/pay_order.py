# -*- coding=utf-8 -*-
import datetime
import random
import os
import socket
import sys
import threading
import time

import wrapcache

from agency.cdn_utils import CDNProxy
from config import urlConf, configCommon
from config.AutoSynchroTime import autoSynchroTime
from config.TicketEnmu import ticket
from config.configCommon import seat_conf
from config.configCommon import seat_conf_2
from config.ticketConf import _get_yaml
from init.login import GoLogin
from inter.AutoSubmitOrderRequest import autoSubmitOrderRequest
from inter.CheckUser import checkUser
from inter.GetPassengerDTOs import getPassengerDTOs
from inter.LiftTicketInit import liftTicketInit
from inter.PayOrder import payOrder
from inter.Query import query
from inter.SubmitOrderRequest import submitOrderRequest
from myException.PassengerUserException import PassengerUserException
from myException.UserPasswordException import UserPasswordException
from myException.ticketConfigException import ticketConfigException
from myException.ticketIsExitsException import ticketIsExitsException
from myException.ticketNumOutException import ticketNumOutException
from myUrllib.httpUtils import HTTPClient
from utils.timeUtil import time_to_minutes, minutes_to_time


#导入webdriver
from selenium import webdriver
import time

#要想调用键盘按键操作需要引入keys包
from selenium.webdriver.common.keys import Keys

#调用环境变量指定的PhantomJS浏览器创建浏览器对象
driver = webdriver.Chrome()
driver.set_window_size(1366, 768)


try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except NameError:
    pass


class payorder:
    """
    快速提交车票通道
    """

    def __init__(self):
        self.from_station, self.to_station, self.station_dates, self._station_seat, self.is_more_ticket, \
        self.ticke_peoples, self.station_trains, self.ticket_black_list_time, \
        self.order_type, self.is_by_time, self.train_types, self.departure_time, \
        self.arrival_time, self.take_time, self.order_model, self.open_time, self.is_proxy = self.get_ticket_info()
        self.is_auto_code = _get_yaml()["is_auto_code"]
        self.auto_code_type = _get_yaml()["auto_code_type"]
        self.is_cdn = _get_yaml()["is_cdn"]
        self.httpClint = HTTPClient(self.is_proxy)
        self.urls = urlConf.urls
        self.login = GoLogin(self, self.is_auto_code, self.auto_code_type)
        self.cdn_list = []
        self.queryUrl = "leftTicket/queryZ"
        self.passengerTicketStrList = ""
        self.oldPassengerStr = ""
        self.set_type = ""

    def get_ticket_info(self):
        """
        获取配置信息
        :return:
        """
        ticket_info_config = _get_yaml()
        from_station = ticket_info_config["set"]["from_station"]
        to_station = ticket_info_config["set"]["to_station"]
        station_dates = ticket_info_config["set"]["station_dates"]
        set_names = ticket_info_config["set"]["set_type"]
        set_type = [seat_conf[x.encode("utf-8")] for x in ticket_info_config["set"]["set_type"]]
        is_more_ticket = ticket_info_config["set"]["is_more_ticket"]
        ticke_peoples = ticket_info_config["set"]["ticke_peoples"]
        station_trains = ticket_info_config["set"]["station_trains"]
        ticket_black_list_time = ticket_info_config["ticket_black_list_time"]
        order_type = ticket_info_config["order_type"]

        # by time
        is_by_time = ticket_info_config["set"]["is_by_time"]
        train_types = ticket_info_config["set"]["train_types"]
        departure_time = time_to_minutes(ticket_info_config["set"]["departure_time"])
        arrival_time = time_to_minutes(ticket_info_config["set"]["arrival_time"])
        take_time = time_to_minutes(ticket_info_config["set"]["take_time"])

        # 下单模式
        order_model = ticket_info_config["order_model"]
        open_time = ticket_info_config["open_time"]

        # 代理模式
        is_proxy = ticket_info_config["is_proxy"]

        print(u"*" * 50)
        print(u"检查当前python版本为：{}，目前版本只支持2.7.10-2.7.15".format(sys.version.split(" ")[0]))
        print(u"12306刷票小助手，最后更新于2019.01.08，请勿作为商业用途，交流群号：286271084(已满)， 2群：649992274(已满)，请加3群(未满)， 群号：632501142、4群(未满)， 群号：606340519")
        if is_by_time:
            method_notie = u"购票方式：根据时间区间购票\n可接受最早出发时间：{0}\n可接受最晚抵达时间：{1}\n可接受最长旅途时间：{2}\n可接受列车类型：{3}\n" \
                .format(minutes_to_time(departure_time), minutes_to_time(arrival_time), minutes_to_time(take_time),
                        " , ".join(train_types))
        else:
            method_notie = u"购票方式：根据候选车次购买\n候选购买车次：{0}".format(",".join(station_trains))
        print (u"当前配置：\n出发站：{0}\n到达站：{1}\n乘车日期：{2}\n坐席：{3}\n是否有票优先提交：{4}\n乘车人：{5}\n" \
               u"刷新间隔: 随机(1-3S)\n{6}\n僵尸票关小黑屋时长: {7}\n下单接口: {8}\n下单模式: {9}\n预售踩点时间:{10} ".format \
                (
                from_station,
                to_station,
                station_dates,
                ",".join(set_names),
                is_more_ticket,
                ",".join(ticke_peoples),
                method_notie,
                ticket_black_list_time,
                order_type,
                order_model,
                open_time,
            ))
        print (u"*" * 50)
        return from_station, to_station, station_dates, set_type, is_more_ticket, ticke_peoples, station_trains, \
               ticket_black_list_time, order_type, is_by_time, train_types, departure_time, arrival_time, take_time, \
               order_model, open_time, is_proxy

    def station_table(self, from_station, to_station):
        """
        读取车站信息
        :param station:
        :return:
        """
        path = os.path.join(os.path.dirname(__file__), '../station_name.txt')
        result = open(path)
        info = result.read().split('=')[1].strip("'").split('@')
        del info[0]
        station_name = {}
        for i in range(0, len(info)):
            n_info = info[i].split('|')
            station_name[n_info[1]] = n_info[2]
        from_station = station_name[from_station.encode("utf8")]
        to_station = station_name[to_station.encode("utf8")]
        return from_station, to_station

    def call_login(self, auth=False):
        """
        登录回调方法
        :return:
        """
        if auth:
            return self.login.auth()
        else:
            self.login.go_login()

    def cdn_req(self, cdn):
        for i in range(len(cdn) - 1):
            http = HTTPClient(0)
            urls = self.urls["loginInitCdn"]
            http._cdn = cdn[i].replace("\n", "")
            start_time = datetime.datetime.now()
            rep = http.send(urls)
            if rep and "message" not in rep and (datetime.datetime.now() - start_time).microseconds / 1000 < 500:
                if cdn[i].replace("\n", "") not in self.cdn_list:  # 如果有重复的cdn，则放弃加入
                    # print(u"加入cdn {0}".format(cdn[i].replace("\n", "")))
                    self.cdn_list.append(cdn[i].replace("\n", ""))
        print(u"所有cdn解析完成...")

    def cdn_certification(self):
        """
        cdn 认证
        :return:
        """
        if self.is_cdn == 1:
            CDN = CDNProxy()
            all_cdn = CDN.open_cdn_file()
            if all_cdn:
                # print(u"由于12306网站策略调整，cdn功能暂时关闭。")
                print(u"开启cdn查询")
                print(u"本次待筛选cdn总数为{}, 筛选时间大约为5-10min".format(len(all_cdn)))
                t = threading.Thread(target=self.cdn_req, args=(all_cdn,))
                t.setDaemon(True)
                # t2 = threading.Thread(target=self.set_cdn, args=())
                t.start()
                # t2.start()
            else:
                raise ticketConfigException(u"cdn列表为空，请先加载cdn")

    def main(self):
        autoSynchroTime()  # 同步时间
        self.cdn_certification()
        l = liftTicketInit(self)
        l.reqLiftTicketInit()
        self.call_login()
        #检查用户登录, 检查间隔为2分钟
        check_user = checkUser(self)
        t = threading.Thread(target=check_user.sendCheckUser)
        t.setDaemon(True)
        t.start()
        from_station, to_station = self.station_table(self.from_station, self.to_station)

        print("********OKOKOKOKOKO******")
        driver.get("https://kyfw.12306.cn/otn/view/train_order.html")
        #获取页面名为wraper的id标签的文本内容
        data = driver.page_source
        print data
        driver.quit()
        #打印数据内容
        print(data)

        num = 0
        while 1:
            try:
                num += 1
                now = datetime.datetime.now()  # 感谢群里大佬提供整点代码
                configCommon.checkSleepTime(self)   # 晚上到点休眠
                if self.order_model is 1:
                    sleep_time_s = 0.5
                    sleep_time_t = 0.6
                    # 测试了一下有微妙级的误差，应该不影响，测试结果：2019-01-02 22:30:00.004555，预售还是会受到前一次刷新的时间影响，暂时没想到好的解决方案
                    while not now.strftime("%H:%M:%S") == self.open_time:
                        now = datetime.datetime.now()
                        if now.strftime("%H:%M:%S") > self.open_time:
                            break
                        time.sleep(0.0001)
                else:
                    sleep_time_s = 0.5
                    sleep_time_t = 3
                # pay = payOrder(self)
                # pay.reqPayorder()
                
            except PassengerUserException as e:
                print(e)
                break
            except ticketConfigException as e:
                print(e)
                break
            except ticketIsExitsException as e:
                print(e)
                break
            except ticketNumOutException as e:
                print(e)
                break
            except UserPasswordException as e:
                print(e)
                break
            except ValueError as e:
                if e == "No JSON object could be decoded":
                    print(u"12306接口无响应，正在重试")
                else:
                    print(e)
            except KeyError as e:
                print(e)
            except TypeError as e:
                print(u"12306接口无响应，正在重试 {0}".format(e))
            except socket.error as e:
                print(e)


if __name__ == '__main__':
    s = select()
    cdn = CDNProxy().open_cdn_file()
    s.cdn_req(cdn)
