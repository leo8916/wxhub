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
    baidu_pan_links
    whole_page
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
    def err_msg(self):
        return self.base_resp['err_msg']

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
    todo = load_todo_list(Input.fake_name)
    if not todo:
        todo['data'] = {}
    data = todo['data']
    mask = list(todo['__mask'] if '__mask' in todo else '')
    last_total = len(mask)
    last_searched = sum(map(lambda x: 1 if x == '1' else 0, mask))

    begin = 0
    pagesize = 5
    total = 0
    while(True):
        time.sleep(0.3)
        if mask and total:
            skip = True
            for i in range(begin, len(mask)):
                if mask[i] == '0':
                    begin = int(i / pagesize) * pagesize
                    skip = False
                    break
            if skip:
                break

        rep = requests.get(Urls.query_arti.format(token=Session.token, fakeid=fakeid, begin=begin, count=pagesize, query=query), cookies=Session.cookies, headers=Session.headers)
        artis = ArtisResp(rep.text)
        if artis.ret :
            print(f"调用搜索, 报错:{artis.ret} {artis.err_msg}")
            break

        if not total:
            '''first loop'''
            total = artis.total
            print(f"正在获取全部链接, 共发现 {artis.total} 条文章, 需要翻页 {artis.total/pagesize + 1} 次, 请稍后 ...")
            if not total:#no artis actualy...
                break
            
            if total == last_searched: #unnecessary search in this time...
                break
            
            if total > last_total:#exsit new artis ...
                mask = (total - last_total) * '0' + mask
        
        index = 0
        for it in artis.list:
            mask[begin + index] = '1'
            index += 1
            link = it['link']
            if link in Input.arti_cache:
                continue
            if link in data:
                continue
            data[link] = it
        begin += artis.count
    
    curr_searched = sum(map(lambda x: 1 if x == '1' else 0, mask))
    # if not total:
    #     raise Exception('搜索不到文章, 或者接口被反爬, 请删除cookies.json文件 等几分钟再试, 或换个账号试试.')
    print(f"本次搜索到{total}条文章, 新增{curr_searched - last_searched}, 共在 todo.list 中包含 {len(data)} 条文章链接 ...")

    todo['__mask'] = ''.join(mask)
    save_todo_list(Input.fake_name, todo)
    cnt = 0
    for url, arti_info in data.items():
        if url in Input.arti_cache:
            continue   
        print(f"{arti_info['title']} --> {url}")
        if pipe_crawl_articles(arti_info):
            cnt += 1
            append_arti_cache(url)

    print(f" 本次共处理了 {cnt} 条文章链接!")

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
        return True
    except:
        print(f"failed crawl images from url:{url}")
        return False

def crawl_baidu_pan_link(url, sdir, url_cache):
    pat = re.compile(r'链接:(https://pan\.baidu\.com/.*?)提取码:(....)')
    try:
        urls = []
        rep = requests.get(url, cookies=Session.cookies, headers=Session.headers)
        html = rep.text
        mats = pat.findall(html, pos=0)
        if not mats:
            return False
        with open("baidu.pan.links.txt", "a") as myfile:
            for uus in mats:
                uu = uus[0]
                if not uu or uu in Input.url_cache:
                    continue
                pwd = uus[1]
                myfile.write(f"{uu} => {pwd}\n") 
                Input.url_cache[uu] = True
                urls.append(uu)
        append_url_cache(urls)
        return True
    except:
        print(f"failed crawl images from url:{url}")
        return False

def crawl_whole_page(url, sdir, url_cache):
    try:
        rep = requests.get(url, cookies=Session.cookies, headers=Session.headers)
        if rep.status_code != 200:
            return False
        html = rep.text
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, 'index.html'), "w") as f:
            f.write(html)
            f.flush()
        return crawl_all_images(url, sdir, Input.url_cache)
    except:
        print(f"failed crawl images from url:{url}")
        return False


def pipe_crawl_articles(arti_info):
    title_4_dir = arti_info['title'].replace(':', '').replace(' ', '').replace(':', '').replace('/', '').replace('|', '').replace('<', '').replace('>', '').replace('?', '').replace('"', '')
    sdir = os.path.join(Input.out_dir, Input.fake_name, title_4_dir)
    if not os.path.exists(sdir):
        os.makedirs(sdir, exist_ok=True)
    if Input.crawl_method == 'all_images':
        return crawl_all_images(arti_info['link'], sdir, Input.url_cache)
    elif Input.crawl_method == 'baidu_pan_links':
        return crawl_baidu_pan_link(arti_info['link'], sdir, Input.url_cache)
    elif Input.crawl_method == 'whole_page':
        return crawl_whole_page(arti_info['link'], sdir, Input.url_cache)

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

def load_todo_list(key):
    fn = os.path.join('output', key, "todo.list")
    if os.path.isfile(fn):
        with open(fn, 'rb') as fi:
            return json.load(fi)
    return {}

def save_todo_list(key, dic):
    if not dic:
        return
    fn = os.path.join('output', key, "todo.list")
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    open(fn, 'wb').write(json.dumps(dic).encode('utf-8'))

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


def test():
    Input.fake_name = '影想'
    Input.crawl_method = 'whole_page'
    main(None)

if __name__ == '__main__':
    # test()
   
    description = u"公众号文章全搞定"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-biz', dest='biz', type=str, help='必填:公众号名字', required=True)
    parser.add_argument('-chrome', dest='chrome', type=str, help='可选:web chrome 路径, 默认使用脚本同级目录下的chromedriver')
    parser.add_argument('-arti', dest='arti', type=str, help='可选:文章名字, 默认处理全部文章')
    parser.add_argument('-method', dest='method', type=str, help='可选, 处理方法:  all_images, baidu_pan_links, whole_page')

    args = parser.parse_args()
    Input.fake_name = args.biz
    Input.crawl_method = args.method if args.method else 'all_images'
    main(args.chrome)