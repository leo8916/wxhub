# -*- coding: utf-8 -*-
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import requests
import re
import shutil
import os
import json
import argparse
import traceback
import random

class Input:
    fake_name = ""#"影想"
    out_dir = "output"
    '''
    all_images
    dump_urls
    '''
    crawl_method = "all_images"
    url_cache = {}
    arti_cache = {}

class Session:
    token = ''
    cookies = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}

class Urls:
    index = 'https://mp.weixin.qq.com'
    editor = 'https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=10&isMul=1&isNew=1&share=1&lang=zh_CN&token={token}'
    query_biz = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&token={token}&lang=zh_CN&f=json&ajax=1&random={random}&query={query}&begin={begin}&count={count}'
    query_arti = 'https://mp.weixin.qq.com/cgi-bin/appmsg?token={token}&lang=zh_CN&f=json&%E2%80%A65&action=list_ex&begin={begin}&count={count}&query={query}&fakeid={fakeid}&type=9'

class BaseResp:
    def __init__(self, sjson):
        self.data = json.loads(sjson)
        self.base_resp = self.data['base_resp']
        
    @property
    def ret(self):
        return self.base_resp['ret']

    @property
    def is_ok(self):
        return self.base_resp['ret'] == 0


class FakesResp(BaseResp):
    
    def __init__(self, sjson):
        super(FakesResp, self).__init__(sjson)
        self.list = self.data['list']
        self.total = self.data['total']

    @property
    def count(self):
        return len(self.list)
    

class ArtisResp(BaseResp):

    def __init__(self, sjson):
        print(sjson)
        super(ArtisResp, self).__init__(sjson) 
        self.list = self.data['app_msg_list'] if self.is_ok else []
        self.total = self.data['app_msg_cnt'] if self.is_ok else 0

    @property
    def count(self):
        return len(self.list)



def execute_times(driver, times):
    for i in range(times + 1):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

def login(driver):
    pass

def read_url_set():
    ret = {}
    fn = os.path.join('output', '__urls.json')
    if os.path.isdir('output') and os.path.isfile(fn):
        with open(fn, 'rt') as f:
            ret = json.load(f)
    return ret

def write_url_set(urls):
    fn = os.path.join('output', '__urls.json')
    if not os.path.isdir('output'):
        shutil.os.makedirs('output', exist_ok=True)
    with open(fn, 'wb') as f:
        f.write(json.dumps(urls).encode('utf-8'))

def set_cookies(driver, cookies):
    Session.cookies = {}
    for item in cookies:
        driver.add_cookie(item)
        Session.cookies[item['name']]=item['value']


def download(url, sname):    
    for i in range(0, 3):
        result = requests.get(url, headers=Session.headers, stream=True)
        if result.status_code == 200:
            with open(sname, 'wb') as f:
                for chunk in result.iter_content(1024):
                    f.write(chunk)
            return True
        else:
            continue
    print(f"Error download:{url}")
    return False
    
def pipe_fakes(fake_name):
    begin = 0
    count = 5
    while(True):
        rep = requests.get(Urls.query_biz.format(random=random.random(), token=Session.token, query=fake_name, begin=begin, count=count), cookies=Session.cookies, headers=Session.headers)
        fakes = FakesResp(rep.text)
        if not fakes.is_ok:
            break
        i = 0
        for it in fakes.list:
            print(f"{i}) {it['nickname']}")
            i = i + 1
        
        ic = input("choose index or next page(n):") 
        if ic == 'n' or ic == 'N':
            begin = begin + fakes.count
            continue
        return fakes.list[int(ic)]
    
def pipe_articles(fakeid, query=''):
    begin = 0
    pagesize = 5
    cnt = 0
    while(True):
        rep = requests.get(Urls.query_arti.format(token=Session.token, fakeid=fakeid, begin=begin, count=pagesize, query=query), cookies=Session.cookies, headers=Session.headers)
        artis = ArtisResp(rep.text)
        if not artis.total:
            break
        for it in artis.list:
            link = it['link']
            cnt += 1
            if link in Input.arti_cache:
                continue
            print(f"{it['title']} --> {link}")
            pipe_crawl_articles(it)
            append_arti_cache(link)
            # time.sleep(0.3)
        begin += artis.count
        continue

    print(f"{cnt} articles processed!")

def crawl_all_images(url, sdir, url_cache):
    pat = re.compile(r'src="(https://.*?)"')
    urls = []
    try:
        rep = requests.get(url, cookies=Session.cookies, headers=Session.headers)
        html = rep.text
        mats = pat.findall(html, pos=0)
        idx = 0
        for m in mats:
            if m in url_cache:
                continue
            download(m, os.path.join(sdir, f"{idx}.jpg"))
            urls.append(m)
            idx += 1
        append_url_cache(urls)
    except:
        print(f"failed crawl images from url:{url}")


def pipe_crawl_articles(arti_info):
    sdir = os.path.join(Input.out_dir, Input.fake_name, arti_info['title'])
    if not os.path.exists(sdir):
        os.makedirs(sdir, exist_ok=True)
    if Input.crawl_method == 'all_images':
        crawl_all_images(arti_info['link'], sdir, Input.url_cache)


def pipe():
    '''query fakes '''
    fake_info = pipe_fakes(Input.fake_name)
    if not fake_info:
        raise Exception(f"Can not query fakes with input:{Input.fake_name}")
    '''query arti'''
    fakeid = fake_info['fakeid']
    pipe_articles(fakeid)
    input("pipe contiune:")


def process_input():
    Input.artis_cache = {}
    ac = os.path.join('arti.cache.list')
    if os.path.isfile(ac):
        with open(ac, 'rt') as fi:
            line = fi.readline()
            while line:
                Input.arti_cache[line.strip()] = True
                line = fi.readline()
        
    uc = os.path.join('url.cache.list')
    if os.path.isfile(uc):
        with open(uc, 'rt') as fi:
            line = fi.readline()
            while line:
                Input.url_cache[line.strip()] = True
                line = fi.readline()


def append_arti_cache(arti_link):
    arti_link = arti_link.strip()
    if not arti_link:
        return
    ac = os.path.join('arti.cache.list')
    with open(ac, "a") as myfile:
        myfile.write(f"{arti_link}\n")
        Input.arti_cache[arti_link] = True

def append_url_cache(urls):
    ac = os.path.join('url.cache.list')
    with open(ac, "a") as myfile:
        for url in urls:
            url = url.strip()
            if not url:
                continue
            myfile.write(f"{url}\n") 
            Input.url_cache[url] = True


def repipe():
    process_input()
    i = 0
    for k, v in Input.url_cache.items():
        download(k, os.path.join('output', f"{i}.jpg"))
        i += 1

def main(chrome):
    #会过期, 重新登录后需要重新取得
    if not chrome:
        if os.path.isfile('chromedriver'):
            chrome = 'chromedriver'
        else:
            chrome = input('输入webchrome:').strip()
    driver = webdriver.Chrome(executable_path=chrome)
    cookies = json.load(open('cookies.json', 'rb')) if os.path.isfile('cookies.json') else []
    driver.get(Urls.index)
    if not cookies:
        input("请先手动登录, 完成后按回车继续:")
        cookies = driver.get_cookies()
        open('cookies.json', 'wb').write(json.dumps(cookies).encode('utf-8'))

    set_cookies(driver, cookies)
    driver.get(Urls.index)
    url = driver.current_url
    if 'token' not in url:
        raise Exception(f"获取网页失败!")
    Session.token = re.findall(r'token=(\w+)', url)[0]
    process_input()
    pipe()

if __name__ == '__main__':
    # repipe()
    description = u"公众号文章全搞定"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-biz', dest='biz', type=str, help='必填:公众号名字', required=True)
    parser.add_argument('-chrome', dest='chrome', type=str, help='可选:web chrome 路径, 默认使用脚本同级目录下的chromedriver')
    parser.add_argument('-arti', dest='arti', type=str, help='可选:文章名字, 默认处理全部文章')

    args = parser.parse_args()
    Input.fake_name = args.biz
    main(args.chrome)