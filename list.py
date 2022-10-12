import threading
import requests, time
from multiprocessing import Queue
from mongo_db import ipmongo
import json
from myran import myran
import random
from lxml import etree
import re
import ddddocr

#创建多线程子类
class Proxy(threading.Thread):
    def __init__(self, proxy_name, proxy_queue,data_queue, time_start):
        #用于调用父类
        super().__init__()
        self.proxy_queue = proxy_queue
        self.data_queue = data_queue
        self.proxy_name = proxy_name
        self.time_start = time_start
    def run(self):
        #print("%s开启了"%self.proxy_name ,end="")
        while not proxy_state:
            header = {
                "User-Agent": myran.agents()
            }
            # print(header)
            try:
                proxy_i = self.proxy_queue.get(block=False)
                #print(proxy_i)
                ipresponse = requests.get(url=proxy_i["url"],headers=header,timeout=4)
                #print(proxy_i["url"],ipresponse.status_code)
                time.sleep(random.random())  # 随机等待时间
                #print(ipresponse.status_code)
                if ipresponse.status_code == 200:
                    ipresponse.encoding = requests.utils.get_encodings_from_content(ipresponse.text)[0]# 修改encoding 避免中文乱码
                    self.parse(proxy_i,ipresponse.text)
                    #print(proxy_i["url"])
            except Exception as e:
                pass
                #print(e.__traceback__.tb_frame.f_globals["__file__"],e,e.__traceback__.tb_lineno)
            
    #处理xpath拿到数据
    def parse(self,proxy,htmltext):
        try:
            ip_html = etree.HTML(htmltext)
            tr_list = ip_html.xpath(proxy["xpath"])
            ip_list = []
            #print("tr列表长度：" + str(len(tr_list)))
            for tr in tr_list:
                ip_dict = {}
                #print(tr.xpath(proxy["xpath_anonymous"]))
                if len(tr.xpath(proxy["xpath_anonymous"]))!=0:
                    ip_dict["anonymous"] = tr.xpath(proxy["xpath_anonymous"])[0]
                else:ip_dict["anonymous"]=""
                # print(ip_dict["anonymous"])
                anonymous_i = ip_dict["anonymous"].find("匿")
                #if anonymous_i != -1:
                if True:#anonymous_i ==True:
                    ip_dict["ip"] = tr.xpath(proxy["xpath_ip"])[0]
                    ip_dict["port"] = tr.xpath(proxy["xpath_port"])[0]
                    #print(ip_dict["port"])
                    if ip_dict["ip"].find(":") != -1:
                        ip_dict["ip"] = (re.findall("(.*?):", ip_dict["ip"]))[0]

                    if proxy['state'] != 'image':  #如果是图片 用ddddocr识别
                        if ip_dict["port"].find(":") != -1:
                            ip_dict["port"] = (re.findall(":(\d+)", ip_dict["port"]))[0]

                    else:
                        image_url = proxy['url_main'] + ip_dict["port"]
                        try:
                            ocr = ddddocr.DdddOcr(show_ad=False)
                            response= requests.get(image_url,headers={"User-Agent":myran.agents()})
                            res=ocr.classification(response.content)
                            ip_dict["port"]=res
                            #print(ip_dict["port"],res,proxy)
                        except Exception as e:
                            print(e.__traceback__.tb_lineno,e)

                    ip_dict["ip"] = re.sub(r'\n','',ip_dict["ip"])
                    ip_dict["type"] = tr.xpath(proxy["xpath_type"])[0]
                    if len(tr.xpath(proxy["xpath_country"]))!=0:
                        ip_dict["country"] = tr.xpath(proxy["xpath_country"])[0]
                    else:ip_dict["country"]=""
                    ip_dict['url_main']=proxy['url_main']
                    self.data_queue.put(ip_dict)

            return ip_list
        except Exception as e:
            print("parse失败",proxy["url"],e.__traceback__.tb_frame.f_globals["__file__"],e,e.__traceback__.tb_lineno)

#检查ip的可用性
class Data_thread(threading.Thread):
    def __init__(self, data_name,data_queue):
        super().__init__()
        self.data_name=data_name
        self.data_queue=data_queue

    def run(self):
        #print(self.data_name + "开启了",end="")
        while not data_state:
            try:
                data=self.data_queue.get(block=False)

            except Exception as e:
                pass
            try:
                header={
                    "User-Agent":myran.agents()
                    }
                proxies = {
                    "http": data['ip']+":"+data["port"],
                    "https": data['ip']+":"+data["port"]
                }
                print('proxies',proxies)
                response = requests.get("https://www.ip138.com/",proxies=proxies, headers=header, timeout=5)
                response.raise_for_status()
                print("可用IP:",data)
                if ipmongo.count_ip(data['ip'])==0:
                    ipmongo.insert_one(data)
            except requests.HTTPError as e:
                print('HTTPError', proxies, e)
            except Exception as e:
                pass
                #print('Exception', proxies, e)


                    

#全局变量 监视资源是否为空 默认False
proxy_state = False
data_state=False
tmp_num=0

def main():
    global proxy_state,page_state,data_state
    header = {
        "User-Agent": myran.agents()
    }
    #ipmongo.removeall()  #清空mongodb
    
    #提取data.json数据
    daililist=[]
    with open("data.json","r") as f:
        daililist =json.loads(f.read())     #json数据转成list
        #print(daililist)
    proxy_queue = Queue()
    data_queue=Queue()

    #遍历、拼接所有网站的页面url并且put进proxy_queue
    #procy_name_list用来构成线程名启动多线程
    procy_name_list = []
    for web in daililist:
        try:
            response = requests.get(web["url_main"],headers=header,timeout=5)

            if response.status_code==200:
                #print(int(web["pages"]))
                for i in range(1, int(web["pages"]) + 1):

                    web["url"] = web["url_t"] + str(i) + web["url_d"]  # 网站翻页url拼接
                    #print(web)
                    temp = web.copy()
                    # print(id(temp)==id(web))
                    proxy_queue.put(temp)
                    webname = web["name"]
                    procy_name_list.append(webname + "网站线程")  # 懒得做线程数量控制 一个页面一个线程
        except:print('网址已失效:%s'%web["url_main"])

    print("当前一共%d个网页" % proxy_queue.qsize())

    proxy_thread_list = []
    for proxy_name in procy_name_list: 
        time_start = time.time()
        proxy_thread = Proxy(proxy_name, proxy_queue,data_queue,time_start)
        proxy_thread.start()
        proxy_thread_list.append(proxy_thread)
    time.sleep(1)
    data_name_list = []
    for i in range(1,30):
        data_name_list.append("data线程"+str(i)+"号")
    data_thread_list=[]
    for data_name in data_name_list:
        data_thread = Data_thread(data_name, data_queue)
        data_thread.start()
        data_thread_list.append(data_thread)

    while not proxy_queue.empty():  # 持续判断队列状态
        pass
    #print(" proxy跳出循环了",end="")
    proxy_state = True
    for procy_n in proxy_thread_list:
        procy_n.join()
        #print(procy_n.proxy_name + "结束了",end="")
    while not data_queue.empty():  # 持续判断队列状态
        pass
    #print("data跳出循环了")
    data_state = True
    for data_n in data_thread_list:
        data_n.join()
        #print(data_n.data_name + "结束了",end="")

def ceproxies():
    with open("data.json", "r") as f:
        daililist = json.loads(f.read())
        for i  in  daililist:
            print(i['url_main'])
if __name__ == "__main__":
    # ceproxies()
    main()
    # mainUrl()
