# LRUCache

一个简单的 LRU 缓存装饰器，可以设置缓存大小和过期时间，过期策略采用主动淘汰（定期淘汰）和被动淘汰

该 LRU 缓存是线程安全的，如果你是单线程运行也可以把它关了，以此提高运行速度

定期淘汰策略下有个守护线程负责定期淘汰过期的 key，这会与主线程产生竞争，因此必须开启线程安全

## 使用

```python
>>> from LRUCache import lru_cache
>>> @lru_cache(maxsize=2, expiration=None)
... def f(x):
...     print('call f')
...     return x
... 
>>> f(1)
call f
1
>>> f(1)
1
```



```python
>>> @lru_cache(maxsize=2, expiration=2)
... def f(x):
...     print('call f')
...     return x
... 
>>> f(1)
call f
1
>>> import time
>>> time.sleep(2)
>>> f(1)
call f
1
```

参数说明：

- **maxsize** ：缓存大小，大于等于 0 或者 None，默认为 128。如果为 None，缓存大小将不受限制；如果为0，则没有缓存，直接调用函数返回结果
- **expiration** ：过期时间，大于等于 0 或者 None，默认为 300 秒。如果为 None，key 将永远不会过期；如果为0，key 立即失效
- **cleanup_duration**：定期淘汰时间，大于等于 0 或者 None，默认为 0。如果为 0 或者 None，则不开启定期淘汰，只有被动淘汰
- **thread_safe**：线程安全模式，True 或者 False，默认为 True。如果开启了定期淘汰，即 cleanup_duration > 0，则必须开启线程安全模式，如果不这么做程序会强制开启线程安全。

**lru_cache** 的实现依赖底层的 **LRUCacheDict**，这个 **LRUCacheDict** 可以直接使用，其参数和 **lru_cache** 一样：

```python
>>> cache = LRUCacheDict(maxsize=2, expiration=10)
>>> cache[1] = 1
>>> cache[2] = 2
>>> cache.size()
2
>>> time.sleep(10)
>>> cache[1]
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "E:\Python\MyProjects\LRUCache\LRUCache.py", line 36, in wrapper
    return func(cache, *args, **kwargs)
  File "E:\Python\MyProjects\LRUCache\LRUCache.py", line 88, in __getitem__
    raise KeyError(key)
KeyError: 1
>>> cache.size()
0
>>> cache[1] = 1
>>> cache[2] = 2
>>> cache[3] = 3
>>> cache[1]
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "E:\Python\MyProjects\LRUCache\LRUCache.py", line 36, in wrapper
    return func(cache, *args, **kwargs)
  File "E:\Python\MyProjects\LRUCache\LRUCache.py", line 88, in __getitem__
    raise KeyError(key)
KeyError: 1
```

## 参考

1. [Python-LRU-cache](https://github.com/stucchio/Python-LRU-cache)
2. [functools.lru_cache](https://github.com/python/cpython/blob/3d07c1ee1d2d475b74816117981d6ec752c26c23/Lib/functools.py#L486)

## TODO

- [ ] 丰富测试用例和文档说明
- [ ] 统计命中次数和失效次数并计算命中率

