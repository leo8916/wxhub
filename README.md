## 公众号文章抓取工具
使用公众号文章编辑链接的方案, 突破搜狗方案10条的限制~~~ ;-)


### 准备
- 首先你需要有一个 [微信公众号, 注册很简单](https://mp.weixin.qq.com)
- python 3.6
- [下载web chrome](http://chromedriver.chromium.org/home) 在第一次登陆时, 需要使用其手动登录. 
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
usage: wxhub.py [-h] -biz BIZ [-chrome CHROME] [-arti ARTI]

公众号文章全搞定

optional arguments:
  -h, --help      show this help message and exit
  -biz BIZ        必填:公众号名字
  -chrome CHROME  可选:web chrome 路径, 默认使用脚本同级目录下的chromedriver
  -arti ARTI      可选:文章名字, 默认处理全部文章

```

现有缓存功能, 目前缓存在如下文件中.

- 用户cookies
- 已经爬取的文章链接.  --> arti.cache.list
- 已经下载的链接. 		--> url.cache.list

需要全部重新下载时, 删除对应文件即可.


### Enjoy ;-)
- 使用有疑问, 请联系我: <isyuu4reg@163.com>
- 欢迎投喂: 

![感谢投喂](http://imglf6.nosdn0.126.net/img/aFNNQXFSeWVxNVMydnBDZ01NM0ltWFIwbkpqcFBvb2R6OFNhZEg4QW51dm9lUzBNYWpyb013PT0.jpg)

