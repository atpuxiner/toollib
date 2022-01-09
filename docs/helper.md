## toollib 官方文档

### ToolDecorator

*装饰器工具*

* catch_exception
```
捕获异常
  :param is_raise: 是否raise
  :return:
```

* print_return
```
打印返回结果
  :param is_print: 是否打印
  :return:
```

* timer
```
计时器
  :param func:
  :return:
```



### ToolException

*异常基类*



### ToolG

*全局变量（基于sqlite3实现的key-value容器）*

* clear
```
清除所有key-value
  :return:
```

* delete
```
删除key
  :param key:
  :return:
```

* exists
```
检测key是否存在
  :param key:
  :return:
```

* expire
```
设置key的过期时间
  :param key:
  :param ex: 默认为0（表不设置过期时间）
  :return:
```

* get
```
获取key的value
  :param key:
  :param check_expire: 是否检测过期（True: 若过期则会raise）
  :param get_expire: 是否返回过期时间（True: 返回格式为元组(value, expire)）
  :return:
```

* remove
```
移除实例g的db文件
  :return:
```

* set
```
设置kye-value
  :param key:
  :param value:
  :param expire: 默认为0（表不设置过期时间）
  :return:
```



### ToolSingleton

*单例模式*



### ToolTime

*时间工具*

* now2str
```
now datetime to str
  :param fmt:
  :return:
```

* str2datetime
```
convert str datetime to datetime
  :param time_str:
  :param fmt:
  :return:
```



### ToolUtils

*utils工具*

* get_files
```
获取文件
  :param src_dir: 源目录
  :param pattern: 匹配模式
  :param is_name: 是否获取文件名（True: 获取文件及路径，False: 获取文件名）
  :param is_r: 是否递规查找源目录及子目录所有的文件
  :return:
```

* json
```
json loads or dumps
  :param data:
  :param loadordumps: loads or dumps
  :param default: 默认值（如果入参data为空，优先返回给定的默认值）
  :param args:
  :param kwargs:
  :return:
```


