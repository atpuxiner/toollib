"""
@author axiner
@version v1.0.0
@created 2022/2/8 20:37
@abstract 正则表达式
@description
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
