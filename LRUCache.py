import time
import threading
import functools
import warnings
import weakref
from collections import OrderedDict, namedtuple

LRUItem = namedtuple('LRUItem', ['val', 'expire_time'])


def lru_cache(maxsize=128, expiration=5 * 60, cleanup_duration=0, thread_safe=True):
    """
    :param maxsize: >= 0 or None, if set to None, the cache can grow without bound
    :param expiration: >= 0 or None, if set to None, keys will not expire
    :param cleanup_duration: >= 0 or None, if set to 0 or None, cleanup thread will not start
    :param thread_safe: True or False, if set a cleanup thread, thread safe must open
    :return: a lru decorator
    """

    def decorator(user_func):
        if maxsize == 0:  # No caching
            def wrapper(*args, **kwds):
                return user_func(*args, **kwds)
        else:
            wrapper = LRUCacheWrapper(user_func, LRUCacheDict(maxsize, expiration, cleanup_duration, thread_safe))
        return functools.update_wrapper(wrapper, user_func)

    return decorator


def _lock_decorator(func):
    @functools.wraps(func)
    def wrapper(cache, *args, **kwargs):
        if cache.thread_safe:
            with cache._lock:
                return func(cache, *args, **kwargs)
        else:
            return func(cache, *args, **kwargs)

    return wrapper


class ThreadCleanup(threading.Thread):
    daemon = True

    def __init__(self, cache, duration=1 * 60):
        super().__init__()
        self.duration = duration
        self.ref_cache = weakref.ref(cache)  # use weakref to avoid circular reference

    def run(self):
        while self.ref_cache():  # get the cache
            cache = self.ref_cache()
            if cache:
                next_expire = cache.cleanup()
                if next_expire is None:
                    time.sleep(self.duration)
                else:
                    time.sleep(next_expire + 1)
            cache = None  # manually collect memory to avoid circular reference


class LRUCacheDict:
    def __init__(self, maxsize=128, expiration=5 * 60, cleanup_duration=0, thread_safe=True):
        if cleanup_duration and not thread_safe:
            warnings.warn('Thread cleanup must be run under thread safe, automatically set thread safe!')
            thread_safe = True

        self.maxsize = maxsize if maxsize else float('inf')
        self.expiration = expiration if expiration else float('inf')
        self.thread_safe = thread_safe
        self._cache = OrderedDict()

        if self.thread_safe:
            self._lock = threading.RLock()
        if cleanup_duration:
            ThreadCleanup(self, cleanup_duration).start()  # it's a circular reference

    @_lock_decorator
    def __contains__(self, key):
        self.cleanup()
        return key in self._cache

    @_lock_decorator
    def __getitem__(self, key):
        self.cleanup()
        if key not in self._cache:
            raise KeyError(key)
        self._cache.move_to_end(key)  # expire_time is not updated
        return self._cache[key].val

    @_lock_decorator
    def __setitem__(self, key, val):
        self.__delete__(key)
        self._cache[key] = LRUItem(val, time.time() + self.expiration)
        self.cleanup()

    @_lock_decorator
    def __delete__(self, key):
        if key in self._cache:
            del self._cache[key]

    @_lock_decorator
    def size(self):
        self.cleanup()
        return len(self._cache)

    @_lock_decorator
    def get(self, key, default=None):
        self.cleanup()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key].val
        return default

    @_lock_decorator
    def cleanup(self):
        now = time.time()
        # Delete expired
        next_expire = None
        for k in list(self._cache.keys()):
            if self._cache[k].expire_time < now:
                self.__delete__(k)
            else:
                next_expire = self._cache[k].expire_time
                break
        # If we have more than self.max_size items, delete the oldest
        while len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

        return next_expire - now if next_expire else None


class LRUCacheWrapper:
    def __init__(self, user_func, cache=None):
        self._cache = cache if cache else LRUCacheDict()
        self.user_func = user_func

    def __call__(self, *args, **kwargs):
        key = repr((args, kwargs)) + '#' + self.user_func.__name__  # generate cache key
        res = self._cache.get(key)
        if not res:
            res = self.user_func(*args, **kwargs)
            self._cache[key] = res
        return res
