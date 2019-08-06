#!/usr/bin/env python
# coding: utf-8

import requests
#import Pytesseract//识别验证码的库，暂时不用
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import bs4
import time
import sys

#获取登陆信息
def getInfo():
    #loginname = input("输入学号：")
    #loginmm = input("输入密码：")
    #对输入进行编码，形成encoded，编码函数在conwork.js中，待完善
    safecode = getSafeCode()
    #info = {'userAccount': loginname, 'userPassword':loginmm,'encoded':'ODAwMTcxNjA1OQ==%%%eXpiMTUwMDEz','RANDOMCODE':safecode,'jzmmid':'1'}
    formdata = {'encoded':'ODAwMTcxNjA1OQ==%%%Ynp5MTU3NzA4MTA2NTA=','RANDOMCODE':safecode}
    return formdata

#处理验证码
#可以使用第三方库，但准确率不高，所以弃用，选择让用户自己识别
def getSafeCode():
    pil_im = Image.open('./safecodeimage.jpg')
    plt.figure("safecode",figsize=(2,4))
    plt.imshow(pil_im)
    plt.axis('off')
    plt.show()  
    safecode = input("输入验证码：") 
    return safecode

#登陆
def login():
    #会话
    s = requests.Session()

    #真实登陆地址
    loginUrl = 'http://jwc104.ncu.edu.cn:8081/jsxsd/xk/LoginToXk'

    #验证码地址
    imgurl = 'http://jwc104.ncu.edu.cn:8081/jsxsd/verifycode.servlet'

    #获取验证码图片
    img = s.get(imgurl).content 
    with open('./safecodeimage.jpg','wb') as safeimg:
        safeimg.write(img)

    #获取post数据
    dataF = getInfo()

    #构造报头
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    header = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Content-Length':'65',
        'Content-Type':'application/x-www-form-urlencoded',
        #'Cookie':'',  #需要登录一次后使用
        'Host':'jwc104.ncu.edu.cn:8081',
        'Origin':'http://jwc104.ncu.edu.cn:8081',
        'Proxy-Connection':'keep-alive',
        'Referer':'http://jwc104.ncu.edu.cn:8081/jsxsd/',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

    #向服务器post登陆信息，使用session保存登陆信息，以访问其他页面
    #返回跳转页面信息Response对象
    mainpage = s.post(loginUrl, data = dataF, headers =  header)
    ####testpoint
    #content = mainpage.text
    #print(content)
    ###OK

    #成绩查询地址
    queryurl = 'http://jwc104.ncu.edu.cn:8081/jsxsd/kscj/cjcx_query?Ves632DSdyV=NEW_XSD_XJCJ'

    #进入成绩查询界面, get方法
    query_main = s.get(queryurl)
    ###testpoint
    #content = query_main .text
    #print(content)
    ###OK

    #查询列表地址
    querylisturl = 'http://jwc104.ncu.edu.cn:8081/jsxsd/kscj/cjcx_list'

    #用户输入查询信息
    print("输入时间及学期，1-上学期，2-下学期", end='\n')
    querytime = input("例如：2016-2017-2:")

    kcxz = ['01', '02', '03', '04', '05', '06', '07', 'F1']
    tablearray=[]
    #查询信息字典
    print('Downloading......')
    for ite in kcxz:
        querydic = {'kksj': querytime,#开课时间
                    'kcxz': ite,         #课程性质
                    'kcmc': '',           #课程名称
                    'xsfs': 'all'         #显示方式
                   }

        #向服务器post查询信息
        souresepage = s.post(querylisturl, data = querydic, headers =  header)
        ###testpoint
        #content = souresepage.text
        #print(content)
        ###OK 
        time.sleep(1)
        #获得表格
        ulist = {}
        soup = bs4.BeautifulSoup(souresepage.text,'lxml')
        table_node = soup.find_all('table')
        #print(type(table_node)) 
        tablearray.append(table_node)
    return tablearray

#获取一个ndarray
all_ar = []
def get_raw_info(tablearray):
    try:
        for table_node in tablearray:
            lists = []
            for table in table_node:
                lists.append(table.get_text().split('\n'))
            #测试时bug，如果在别处查询过改年份，且连接没有断开，就会IndexError异常
            del lists[0]
            one = lists[0]
            new_one = []
            for itm in one:
                if itm!='':
                    new_one.append(itm)
            ar = np.array(new_one)
            #ar.reshape(len(new_one)//10,10)
            all_ar.append(ar)
        rawinfo = np.array(all_ar)
        return rawinfo
    except IndexError as e:
        sys.exit(1)
        print("请断开其他访问连接或重新连接...")

def get_info():
    #获得初始信息
    raw_info = get_raw_info(login())
    #info_colums = ['序号' '开课学期' '课程编号' '课程名称' '成绩' '学分' '总学时' '考核方式' '课程属性' '课程性质']
    
    #处理初始信息成字典
    infodata = []
    count = 0
    for i in range(8):
        if len(raw_info[i])>=20:
            onedata = raw_info[i][10:]
            infodata.append(onedata)
            count = count + 1
    info_list = []
    info_dic = {}
    for i in range(count):
        for ii in range(len(infodata[i][3::10].tolist())):
            dic = {infodata[i][3::10].tolist()[ii]:infodata[i][5::10].tolist()[ii]}
            info_dic.update(dic)
        df = pd.DataFrame([info_dic], index=["学分"]) 
    return df

get_info()




