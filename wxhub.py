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
import math
import codecs

class Input:
    fake_name = ""#"影想"
    out_dir = "output"
    '''
    all_images
    baidu_pan_links
    whole_page
    pipe
    '''
    crawl_method = "all_images"
    url_cache = {}
    arti_cache = {}
    page_sleep = 1
    page_limit = -1
    args = {}
    custom_pipe = []

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
        
        while(True):
            ic = input("输入数字, 选择序号;或者输入n翻页:") 
            try:
                if ic == 'n' or int(ic) >= 0 and int(ic) < len(fakes.list):
                    break
            except ValueError:
                print("输入错误, 请重新输入!")
            continue

        if ic == 'n' or ic == 'N':
            begin = begin + fakes.count
            continue
        return fakes.list[int(ic)]



def pipe_articles(fakeid, query=''):
    TIME_SLEEP = Input.page_sleep

    todo = load_todo_list(Input.fake_name)
    if not todo:
        todo['data'] = {}
    data = todo['data']
    mask = list(todo['__mask'] if '__mask' in todo else '')
    last_total = todo['__total_cnt'] if '__total_cnt' in todo else 0

    begin = 0
    pagesize = 5
    total = 0
    total_page = 0
    last_total_page = math.ceil(last_total / pagesize)
    page_limit = Input.page_limit

    rep = requests.get(Urls.query_arti.format(token=Session.token, fakeid=fakeid, begin=begin, count=pagesize, query=query), cookies=Session.cookies, headers=Session.headers)
    artis = ArtisResp(rep.text)
    if not artis.ret and page_limit:
        total = artis.total
        total_page = math.ceil(total / pagesize)

        if total_page > last_total_page:
            mask = (total_page - last_total_page) * ['0'] + mask
        
        if artis.list[0]['link'] in data:
            mask[0] = '0' #has new arti. reset first page.
        print(f"正在获取全部链接, 共发现 {artis.total} 条文章, 需要翻页 {total_page} 次, 请稍后 ...")
        # 当前页为0时必检查下一页..
        for i in range(0, len(mask)):
            if not page_limit:
                break

            if mask[i] == '1':
                continue
            print(f"正在处理第{i}页...")
            time.sleep(TIME_SLEEP)
            rep = requests.get(Urls.query_arti.format(token=Session.token, fakeid=fakeid, begin=i * pagesize, count=pagesize, query=query), cookies=Session.cookies, headers=Session.headers)
            artis = ArtisResp(rep.text)
            if artis.ret :
                break

            flag = True
            for it in artis.list:
                link = it['link']
                if link in data:
                    continue
                flag = False
                data[link] = it
            mask[i] = '1'
            # force check next page.
            if not flag and i < len(mask) - 1:
                mask[i + 1] = '0' 

            #count check limit
            page_limit -= 1
    else:
        print(f"调用搜索, 报错:{artis.ret} {artis.err_msg}")
        
    curr_searched = sum(map(lambda x: 1 if x == '1' else 0, mask))
    # if not total:
    #     raise Exception('搜索不到文章, 或者接口被反爬, 请删除cookies.json文件 等几分钟再试, 或换个账号试试.')
    print(f"本次搜索到:{total_page} 页文章, 已处理:{curr_searched}页, 共在 todo.list 中包含 {len(data)} 条文章链接 ...")
    todo['__total_cnt'] = total
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

def verfy_arti_content(html):
    if not html:
        return False, "从服务器获取失败"
    pat = re.compile(r'<div class="page_msg')
    if not pat.search(html):
        return True, ""
    pat = re.compile(r'<div class="global_error_msg.*?">(.*?)</div', re.MULTILINE| re.DOTALL)
    ms = pat.findall(html)
    if ms:
        return False, ms[0].strip()
    return False, "服务器返回未知错误"

def crawl_all_images(url, sdir, url_cache, html=None):
    pat = re.compile(r'src="(https://.*?)"')
    pat2 = re.compile(r'wx_fmt=(.*)')
    urls = []
    try:
        if not html:
            rep = requests.get(url, cookies=Session.cookies, headers=Session.headers)
            html = rep.text
        mats = pat.findall(html, pos=0)
        idx = 0
        for m in mats:
            if m in url_cache:
                continue
                
            pps = pat2.findall(m)
            if pps:
                postfix = pps[0]
            else:
                postfix = 'jpg'

            download(m, os.path.join(sdir, f"{idx}.{postfix}"))
            urls.append(m)
            idx += 1
        append_url_cache(urls)
        return True
    except:
        print(f"failed crawl images from url:{url}")
        sg = traceback.format_exc()
        print(sg)
        return False

def crawl_baidu_pan_link(url, sdir, url_cache):
    pat = re.compile(r'链接\s*[:|：]\s*(https://pan\.baidu\.com/.*?)提取码\s*[:|：]\s*(....)')
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
        print(f"failed crawl linkss from url:{url}")
        sg = traceback.format_exc()
        print(sg)
        return False

def crawl_whole_page(url, sdir, url_cache):
    try:
        rep = requests.get(url, cookies=Session.cookies, headers=Session.headers)
        if rep.status_code != 200:
            return False
        html = rep.text
        valid, msg = verfy_arti_content(html)
        if not valid:
            raise Exception(f"保存网页失败: {msg}")
        
        os.makedirs(sdir, exist_ok=True)
        with codecs.open(os.path.join(sdir, 'index.html'), "w", 'utf-8') as f:
            f.write(html)
            f.flush()
        return crawl_all_images(url, sdir, Input.url_cache, html=html)
    except:
        print(f"failed crawl page from url:{url}")
        sg = traceback.format_exc()
        print(sg)
        return False

def crawl_by_custom_pipe(url, sdir, url_cache):
    if not Input.custom_pipe:
        sps = (Input.args.pipe if Input.args.pipe else '').split(',')
        for sp in sps:
            Input.custom_pipe.append(__import__(sp.strip()))
    
    for p in Input.custom_pipe:
        urls = p.crawl(url, sdir)
        for url in urls:
            url_cache[url] = True
        return not not urls
    
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
    elif Input.crawl_method == 'pipe': 
        return crawl_by_custom_pipe(arti_info['link'], sdir, Input.url_cache)

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


# def test():
#     Input.fake_name = '大J小D'
#     Input.crawl_method = 'baidu_pan_links'
#     main(None)

if __name__ == '__main__':
    # test()
   
    description = u"公众号文章全搞定"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-biz', dest='biz', type=str, help='必填:公众号名字', required=True)
    parser.add_argument('-chrome', dest='chrome', type=str, help='可选:web chrome 路径, 默认使用脚本同级目录下的chromedriver')
    parser.add_argument('-arti', dest='arti', type=str, help='可选:文章名字, 默认处理全部文章')
    parser.add_argument('-method', dest='method', type=str, help='可选, 处理方法:  all_images, baidu_pan_links, whole_page')
    parser.add_argument('-sleep', dest='sleep', type=str, help='翻页休眠时间, 默认为1即 1秒每页.')
    parser.add_argument('-pipe', dest='pipe', type=str, help='在method指定为pipe时, 该参数指定pipe处理流程. 例如:"pipe_example, pipe_example1, pipe_example2, pipe_example3"')
    parser.add_argument('-pl', dest='page_limit', type=str, help='指定最大翻页次数, 每次同一个公众号, 翻页太多次会被ban, 0:不翻页 只处理todo.list, 默认<0:无限制 >0:翻页次数')

    Input.args = parser.parse_args()
    Input.fake_name = Input.args.biz
    Input.crawl_method = Input.args.method if Input.args.method else 'all_images'
    Input.page_sleep = int(Input.args.sleep) if Input.args.sleep else 1
    Input.page_limit = int(Input.args.page_limit) if Input.args.page_limit else -1
    main(Input.args.chrome)