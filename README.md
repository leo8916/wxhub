## 公众号文章抓取工具
使用公众号文章编辑链接的方案, 突破搜狗方案10条的限制~~~ ;-)

### 2018.12
- 新增公众号内, 百度网盘链接和密码的抓取. (指定method为baidu_pan_links)
- 新增全部html页面抓取方法 -method whole_page
- 添加todo.list 与 mask 变量
```
todo.list 文件记录了公众号下所有文章的链接数据, 因为高频次调用文章搜索/翻页接口会导致被ban.
所以目前的方案是使用mask记录所有索引处理记录, 保证了不会翻页相同位置, 提高了获取新增链接的几率.
```

### 2019.01
- 添加-pl参数, 用来限制每次公众号翻页数目, 每次翻页过多会被ban.建议10以内.
	- N = 0: 不进行翻页, 只讲之前的url重新处理(todo.list) 
	- N < 0: 不限制翻页(默认), 翻到底或者出错时停止.
	- N > 0: 翻页N次.




### 准备
- 首先你需要有一个 [微信公众号, 注册很简单](https://mp.weixin.qq.com)
- python 3.6
- [下载ChromeDriver](http://chromedriver.chromium.org/home) 在第一次登陆时, 需要使用其手动登录. 
- 安装依赖

```
pip install -r requirements.txt
``` 

### 结构
```
wxhub/
├── README.md
├── arti.cache.list		(使用后生成)	
├── chromedriver			(默认macOS版本, windows可另行下载 重命名即可)
├── cookies.json			(使用后生成)
├── gongzhonghao.py		(使用后生成)
├── output				(使用后生成)
├── requirements.txt	
├── url.cache.list		(使用后生成)
└── wxhub.py

```

### 使用
```
(py3) isyuu:wxhub isyuu$ python wxhub.py -h
usage: wxhub.py [-h] -biz BIZ [-chrome CHROME] [-arti ARTI] [-method METHOD]
                [-sleep SLEEP] [-pipe PIPE] [-pl PAGE_LIMIT]

公众号文章全搞定

optional arguments:
  -h, --help      show this help message and exit
  -biz BIZ        必填:公众号名字
  -chrome CHROME  可选:web chrome 路径, 默认使用脚本同级目录下的chromedriver
  -arti ARTI      可选:文章名字, 默认处理全部文章
  -method METHOD  可选, 处理方法: all_images, baidu_pan_links, whole_page
  -sleep SLEEP    翻页休眠时间, 默认为1即 1秒每页.
  -pipe PIPE      在method指定为pipe时, 该参数指定pipe处理流程. 例如:"pipe_example,
                  pipe_example1, pipe_example2, pipe_example3"
  -pl PAGE_LIMIT  指定最大翻页次数, 每次同一个公众号, 翻页太多次会被ban, 0:不翻页 只处理todo.list, 默认<0:无限制
                  >0:翻页次数

```

现有缓存功能, 目前缓存在如下文件中.

- 用户cookies
- 已经爬取的文章链接.  --> arti.cache.list
- 已经下载的链接. 		--> url.cache.list

需要全部重新下载时, 删除对应文件即可.

### 已知问题
- 在某些情况下, cookies里的session过期后, 会导致"获取页面失败!"的错误.(此时参数cookies.json文件即可)
- 提示"搜索过于频繁"问题, 这可能是又有微信对搜索接口存在反爬机制; 目前解决的方案是:删除cookies.json, 换账号登录, 或者等几个小时即可.(未来准备尝试先缓存所有链接再逐条爬取的方式...)




