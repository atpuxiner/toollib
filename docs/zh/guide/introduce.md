## toollib.crypto

@author axiner

@version v1.0.0

@created 2022/2/27 11:46

@abstract 加密

@description

@history

## cmd5

md5 加密
使用示例：

```py
# 1）针对字符
        obj = 'this is toollib'
        cobj = crypto.cmd5(obj)
        # 2）针对文件
        obj = 'D:/tmp/t.txt'
        cobj = crypto.cmd5(obj, is_file=True)
        # ret: 返回obj的md5
        +++++[更多详见参数或源码]+++++
    :param obj: 对象
    :param is_file: 是否针对文件对象
    :param saltstr: 加盐字符串
    :return:
```

## curl

url 加密与解密
使用示例：

```py{1,6-8}
# 加密
        obj = 'https:www.baidu.com/'
        cobj = crypto.curl(obj)
        # 解密
        obj = crypto.curl(cobj, mode=2)
        # res: 返回相应结果
        +++++[更多详见参数或源码]+++++
    :param obj: 对象
    :param mode: 模式（1-加密；2-解密）
    :return:
```

## cbase64

加密与解密
使用示例： # 1）针对字符
```py
obj = b'这是一个示例'
cobj = crypto.cbase64(obj) # 2）针对文件
obj = 'D:/tmp/t.txt'
to_file = 'D:/tmp/t.c'
cobj = crypto.cbase64(obj, to_file=to_file) # 另：解密详见参数 # res: 返回相应结果
+++++[更多详见参数或源码]+++++
:param obj: 对象
:param mode: 模式（1-加密；2-解密）
:param to_file: 输出指定文件（针对 obj 为文件对象）
:param altchars: altchars（2 bytes, 用于指定替换'/'和'+'）
:param validate:
:return:
```

## cdes
des加密与解密（des mode: ECB or CBC）
使用示例：
```py
# 1）针对字符
obj = b'这是一个示例'
deskey = b'asdfhjkl'  #  8 bytes
desiv = b'aaaaaaaa'  # 8 bytes
cobj = crypto.cdes(obj, deskey=deskey, desiv=desiv)
# 2）针对文件
obj = 'D:/tmp/t.txt'
deskey = b'asdfhjkl'  #  8 bytes
desiv = b'aaaaaaaa'  # 8 bytes
to_file = 'D:/tmp/t.c'
        cobj = crypto.cdes(obj, deskey=deskey, desiv=desiv, to_file=to_file)
        # 另：解密详见参数
        # res: 返回相应结果
        +++++[更多详见参数或源码]+++++
    :param obj: 对象
    :param deskey: des key（8 bytes）
    :param desiv: des iv向量（8 bytes）
    :param mode: 模式（1-加密；2-解密）
    :param to_file: 输出指定文件（针对obj为文件对象）
    :param desmode: des mode (ECB or CBC, 默认为 CBC)
    :param despadmode: despad mode (PAD_NORMAL or PAD_PKCS5, 默认为 PAD_PKCS5)
    :return:
```



## print_return
打印返回结果
使用示例：
@decorator.print_return()
def foo():
return 'this is toollib'
:param is_print: 是否打印
:return:

catch_exception
捕获异常
使用示例：
@decorator.catch_exception()
def foo():
pass
:param is_raise: 是否 raise
:return:

timer
计时器
使用示例：
@decorator.timer()
def foo():
pass
:param func:
:return:

sys_required
系统要求
使用示例：
@decorator.sys_required()
def foo():
pass
:param supported_sys: 支持的系统（正则表达示）
:return:

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.kvalue
@author axiner
@version v1.0.0
@created 2021/12/18 22:21
@abstract key-value 容器（基于 sqlite3）
@description
@history

---

KV
key-value 容器
使用示例： # 创建一个 kv 实例
kv = kvalue.KV(kvfile='D:/tmp/kv.db') # 增改查删操作
kv.set(key='name', value='xxx')
kv.expire(key='name', ex=60) # 过期时间
kv.get(key='name')
kv.exists(key='name')
kv.delete(key='name') # res: 结果存储于 kvfile 的 db 文件里
+++++[更多详见参数或源码]+++++

KV.clear
清除所有 key-value
:return:

KV.delete
删除 key
:param key:
:return:

KV.exists
检测 key 是否存在
:param key:
:return:

KV.expire
设置 key 的过期时间
:param key:
:param ex: 默认为 0（表不设置过期时间）
:return:

KV.get
获取 key 的 value
:param key:
:param check_expire: 是否检测过期（True: 若过期则会 raise）
:param get_expire: 是否返回过期时间（True: 返回格式为元组(value, expire)）
:return:

KV.remove
移除 KV 实例的 kvfile 文件
:return:

KV.set
设置 kye-value
:param key:
:param value:
:param expire: 默认为 0（表不设置过期时间）
:return:

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.regexp
@author axiner
@version v1.0.0
@created 2022/2/8 20:37
@abstract 正则表达式
@description
有以下正则表达式：
1）中文，regexp.zh
2）表情：regexp.emoji

        3）手机号：regexp.phone
        4）座机号（有‘-’）：regexp.landline
        5）座机号（‘-’可有可无）：regexp.landline2
        6）手机号和座机号：regexp.phone_and_landline

        7）邮箱：regexp.email
        8）邮箱（可含中文字符）：regexp.email_contain_zh

        9）ipv4: regexp.ipv4
        10）ipv4（粗匹配）: regexp.ipv4_simple
        11）ipv6（粗匹配）: regexp.ipv6_simple

        12）url: regexp.url

@history

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.useragent
@author axiner
@version v1.0.0
@created 2022/2/8 20:36
@abstract 用户代理
@description
有以下属性：
1）uas 列表 1000 条：useragent.uas
2）从 1000 条 uas 中随机选 1 条：useragent.choice_ua
3）生成 uas: useragent.gen_uas()
@history

---

gen_uas
生成 User-Agent
使用示例：
uas = useragent.gen_uas() # res: 返回 uas 生成器
+++++[更多详见参数或源码]+++++
:param max_len:
:return:

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.utils
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract 实用工具
@description
@history

---

Singleton
单例模式
使用示例： # 比如使类 A 为单例模式
class A(metaclass=utils.Singleton):
pass # res: 得到一个单例类 A

Chars
字符
使用示例： # 比如获取小写字母
low_cases = utils.Chars.lowercases # res: 返回指定的字符
+++++[更多详见参数或源码]+++++

now2str
now datetime to str (获取当前时间的字符串)
使用示例： # 比如获取当前时间
now = utils.now2str() # 比如获取当前日期
now_year = utils.now2str(fmt='d') # 或者 fmt='%Y-%m-%d' # res: 返回指定格式时间的字符串
+++++[更多详见参数或源码]+++++
:param fmt:
:return:

str2datetime
时间字符串转换成日期（默认自动识别 fmt）
使用示例：
time_str = '2021-12-12'
date = utils.str2datetime(time_str) # res: datetime.datetime(2021, 12, 12, 0, 0)
+++++[更多详见参数或源码]+++++
:param time_str: 时间字符串
:param fmt: 格式化
:return:

json
json loads or dumps
使用示例：
data = {'name': 'x', age: 20}
data_json = utils.json(data, mode='dumps') # res: (一个 json)
+++++[更多详见参数或源码]+++++
:param data:
:param mode: loads or dumps
:param default: 默认值（如果入参 data 为空，优先返回给定的默认值）
:param args:
:param kwargs:
:return:

listfile
文件列表
使用示例： # 比如获取某目录下的.py 文件
src_dir = 'D:/tmp'
flist = utils.listfile(src_dir, pattern='\*.py') # res: 输出匹配的文件路径生成器
+++++[更多详见参数或源码]+++++
:param src_dir: 源目录
:param pattern: 匹配模式
:param is_str: 是否返回字符串（True: 若为路径返回字符串，False: 若为路径返回 Path 类型）
:param is_name: 是否获取文件名（True: 返回文件路径，False: 返回文件名）
:param is_r: 是否递规查找
:return:

decompress
解压文件
使用示例： # 比如解压某目录下的.zip 文件
src = 'D:/tmp'
count = utils.decompress(src, pattern='\*.zip') # res: 解压数量
+++++[更多详见参数或源码]+++++
:param src: 源目录或文件
:param dest_dir: 目标目录
:param pattern: 匹配模式（当 src 为目录时生效，默认匹配所有支持的压缩包）
:param is_r: 是否递规查找（当 src 为目录时生效）
:param is_raise: 是否抛异常
:return: count（解压数量）

home
家目录
使用示例：
h = utils.home() # res: 返回家目录的路径
+++++[更多详见参数或源码]+++++
:return:

syscmd
系统命令（基于 subprocess.Popen，具体参数见源）
使用示例： # 比如获取当前路径（linux）
utils.syscmd('pwd') # res: 返回 subprocess.Popen
+++++[更多详见参数或源码]+++++
:param cmd:
:param shell:
:param env:
:param args:
:param kwargs:
:return:

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.validator
@author axiner
@version v1.0.0
@created 2022/3/5 0:03
@abstract 验证器
@description
@history

---

Attr
属性验证（数据描述符）
使用示例：
请查看数据描述符中数据校验.....
+++++[更多详见参数或源码]+++++

choicer
选择验证（校验通过时返回 obj）
使用示例：
flag = 1
flag = validator.choicer(flag, choices=[1,2,3], lable='标识') # res: 若校验不通过则报异常
+++++[更多详见参数或源码]+++++
:param obj: 对象
:param choices: 可选范围
:param lable: 标签
:param errmsg: 不在可选范围时报错信息
:return:

pyv
python 版本校验
使用示例：
pyv = validator.pyv(min_v='3.6') # res: 若校验不通过则报异常
+++++[更多详见参数或源码]+++++
:param min_v: 最小版本号（包含）
:param max_v: 最大版本号（不包含）
:return:

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.webdriver
@author axiner
@version v1.0.0
@created 2022/1/18 21:05
@abstract web 驱动
@description
@history

---

ChromeDriver
谷歌驱动（继承于 selenium） - 可自动下载驱动（注：若指定目录存在与浏览器版本一致的驱动则会跳过）
使用示例： # 1）不指定浏览器版本，则下载当前浏览器对应的版本（针对 win 平台，mac|linux 则下载最新版本）
driver = ChromeDriver()
driver.get('https://www.baidu.com/') # 2）指定浏览器版本（版本号可在浏览器中查看）（注：driver_dir 为驱动器存放目录，可自定义）
driver = ChromeDriver(driver_dir='D:/tmp', version='96.0.4664.45')
driver.get('https://www.baidu.com/')
+++++[更多详见参数或源码]+++++

++++++++++++++++++++++这是分隔线++++++++++++++++++++++
toollib.xlsx
@author axiner
@version v1.0.0
@created 2022/1/23 20:36
@abstract xlsx（基于 openpyxl 库）
@description
@history

---

ws_inserts
插入数据
使用示例：
from openpyxl import load_workbook
wb = load_workbook('D:/tmp/t.xlsx')
ws = wb.active
values = [[1, 2, 3, 4, 5]]
xlsx.ws_inserts(ws, values, index=1)
.....
+++++[更多详见参数或源码]+++++
:param ws: Worksheet 实例（openpyxl 库）
:param values: 值（eg: [[1, 2, 3], [4, 5, 6]]）
:param index: 从哪开始插入值，若为 None 则追加（正整数）
:param mode: 插入模式（r: 插入行值，c: 插入列值）
:param is_new: 是否插入新的行|列（True: 是，False: 否，若有值则会覆盖）
:return:

ws_rows_value
所有行的值
使用示例：
from openpyxl import load_workbook
wb = load_workbook('D:/tmp/t.xlsx')
ws = wb.active
rows = xlsx.ws_rows_value() # res: 返回所有行的值（生成器对象）
+++++[更多详见参数或源码]+++++
:param ws: Worksheet 实例（openpyxl 库）
:return:

ws_cols_value
所有列的值
使用示例：
from openpyxl import load_workbook
wb = load_workbook('D:/tmp/t.xlsx')
ws = wb.active
cols = xlsx.ws_cols_value() # res: 返回所有列的值（生成器对象）
+++++[更多详见参数或源码]+++++
:param ws: Worksheet 实例（openpyxl 库）
:return:

ws_styles
修改样式
使用示例：
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
wb = load_workbook('D:/tmp/t.xlsx')
ws = wb.active
fill = PatternFill(fill_type=None, start_color=’FFFFFF‘, end_color=‘000000’)
styles = {'fill': fill}
xlsx.ws_styles(styles, by_icells='0,0')
.....
+++++[更多详见参数或源码]+++++
注：by_icells |by_cells |by_rows |by_cols，只支持其中一种方式（若传入多则只取第一种方式）
:param ws: Worksheet 实例（openpyxl 库）
:param styles: 样式。以字典形式传入（key 可为：font, fill, border 等）
:param by_icells: 按单元格索引（若索引为 0，则表示从 1 至最大行或列）。eg: '1:2,1:2' >>> 左行：1 至 2 行，右列：1 至 2 列
:param by_cells: 按单元格。eg: 'A1' or ['A1', 'B1', 'C1']
:param by_rows: 按行。eg: 1 or [1, 2, 3]
:param by_cols: 按列。eg: 'A' or ['A', 'B', 'C']
:param exclude_icell: 排除的单元格（by_icells 方式下生效）
:return:
