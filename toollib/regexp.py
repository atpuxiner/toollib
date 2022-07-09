"""
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
"""
# 易混淆
# 1）*: 0次、1次或多次匹配其前的原子
# 2）+: 1次或多次匹配其前的原子
# 3）?: 0次或1次匹配其前的原子
# 4）.: 匹配除换行之外的任何一个字符
# --------------------
zh = r'[\u4e00-\u9fa5]+'
emoji = r'[\u0000-\uFFFF]+'

phone = r'1\d{10}'
landline = r'\d{3}-\d{8}|\d{4}-\d{7}'
landline2 = r'\d{3}-?\d{8}|\d{4}-?\d{7}'
phone_and_landline = landline2

email = r'[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+'
email_contain_zh = r'[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+'

ipv4 = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
ipv4_simple = r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
ipv6_simple = r'(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}'

url = r'(?:https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
