import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import re
import json
from multiprocessing import Pool
import csv
import os
import test1
import time

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
filename='test.csv'
# 存放每一个楼盘的数组
indexurl = []
# 存放每一个楼盘的名称
indexestate = []
url = 'https://newhouse.cnnbfdc.com'
url3 = 'https://newhouse.cnnbfdc.com/project/page_'

def save_csv(items):#写入csv
    if os.path.exists(filename):
        with open(filename, 'a',newline="")as f:
            f_csv = csv.writer(f)
            f_csv.writerows(items)
    else:
        with open(filename, 'w',newline="")as f:
            f_csv = csv.writer(f)
            f_csv.writerows(items)


def get_url_list(url,headers,pattern):#requests+正则表达式，通过url+pattern，返回需要的数据列表
    try:
        time.sleep(1)
        response=requests.get(url,headers=headers)
        print(response.status_code)
        if response.status_code==200:
            print(re.findall(pattern, response.text))
            return re.findall(pattern, response.text)
        else:
            time.sleep(1)
            get_url_list(url, headers, pattern)
    except RequestException:
        return None


def main(offset):
    #url='https://maoyan.com/board/4?offset=0'+str(offset)

    main_fun()

    #print(indexurl)

    pattern = re.compile('<li.*?class="listbody__main__row".*?<a.*?href="(.*?)".*?</a>', re.S)

    #循环每个小区
    for i in range(len(indexurl)):
        #写入小区名
        if i==0:
            with open(filename, 'w', newline="")as f:
                f_csv = csv.writer(f)
                if indexestate[i]:
                    f_csv.writerow(indexestate[i])
        else:
            with open(filename, 'a', newline="")as f:
                f_csv = csv.writer(f)
                if indexestate[i]:
                    f_csv.writerow(indexestate[i])
        url2=indexurl[i]
        pattern2=re.compile('name="spfmenu">.*?<a.*?<a.*?<a.*?<a.*?href="(.*?)".*?>楼盘信息</li>',re.S)
        list2=get_url_list(url2, headers, pattern2)
        #print('list2:'+str(len(list2)))

        url3 = url + list2[0]
        #print('url3:' + url3)
        pattern3 = re.compile('sub-nav-menu__item">.*?href="(.*?)".*?表格模式</span>', re.S)
        list3 = get_url_list(url3, headers, pattern3)
        #使楼栋选项在“不限”上
        pos=list3[0].find('?')
        list3[0]=list3[0][0:pos]

        #获取楼栋列表的html大概位置，方便后续直接通过href获取各楼栋的url
        url4 = url + list3[0]
        print(url4)
        pattern4=re.compile('楼栋.*?不限(.*?)状态',re.S)
        list4=get_url_list(url4, headers, pattern4)
        #print('list4:' + str(len(list4)))

        #获取各个楼栋的URL
        pattern5=re.compile('href="(.*?)"\sclass.*?>(.*?)</a>')
        list5 = re.findall(pattern5, list4[0])
        #循环各个楼栋
        for j in range(len(list5)):
            #将楼栋数据写入csv
            tmp=[]
            tmp.append((list5[j][1],''))
            save_csv(tmp)
            #循环该楼栋下的各页数据
            for k in range(100):
                url6=url + list5[j][0]
                url6 = url6 + "&page=" + str(k + 1)
                print('url6:' + url6)
                pattern6 = re.compile(
                    '<td.*?style="width:20.*?">(.*?)</td>.*?<td>(.*?)</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td>(.*?)</td>',
                    re.S)  # .*?<td>.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td.*?</td>.*?<td>(.*?)</td>
                list6 = get_url_list(url6, headers, pattern6)
                #print(list6)

                if list6:
                    #修改所获取的数据的格式并写入csv
                    list7=[]
                    for m in range(len(list6)):
                        # print(list6[m][2])
                        if '未网签' in list6[m][2]:
                            list7.append((list6[m][0],list6[m][1]+'\t','0'))
                        elif '已网签' in list6[m][2]:
                            list7.append((list6[m][0], list6[m][1] + '\t', '1'))
                        elif '已预定' in list6[m][2]:
                            list7.append((list6[m][0], list6[m][1] + '\t', '2'))
                        else:
                            list7.append((list6[m][0], list6[m][1] + '\t', '3'))
                    save_csv(list7)
                else:
                    break


# 获取每一个页面的整体信息
def get_index_page(url):
    time.sleep(0.1)
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    try:
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print(RequestException)
        return None


# 获取每一个页面具体想要的信息，并进行数据清洗
def index_one_page(html):
    soup = BeautifulSoup(html, "lxml")
    div_arr = soup.find_all(class_='project-title')
    # print(div_arr)
    for div in div_arr:
        try:
            # 拿到页面上所有需要的链接
            tds = div.find_all('a')
            # print(tds)
            for a in tds:
                # print('https://newhouse.cnnbfdc.com'+a.get('href'))
                # print(a.get('href'))
                if a.string == '漫乐荟':
                    indexurl.append(url + a.get('href'))
                    indexestate.append((a.string, ''))
                    break
        except IndexError:
            pass


# 获取网站商品房项目每一页的数据放入indexurl与indexestate中
def index(page,url):
    url = url + str(page)
    # print(url)
    # 获取每一个页面的整体信息
    html = get_index_page(url)
    # 获取每一个页面具体想要的信息，并进行数据清洗
    index_one_page(html)


def main_fun():
    for i in range(1, 20):
        index(i, url3)
    print(indexurl[0])



if __name__=='__main__':
    #for i in range(10):
    #    main(i*10)
    #进程池可以提供指定数量的进程
   # pool=Pool()
   # pool.map(main,[i*10 for i in range(183)])
    #s=input("input")
    #print(s)
    main(0)

