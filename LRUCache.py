import time
import threading
import functools
import warnings
import weakref
from collections import OrderedDict, namedtuple

LRUItem = namedtuple('LRUItem', ['val', 'expire_time'])


def lru_cache(maxsize=128, expiration=5 * 60, cleanup_duration=0, thread_safe=True):
    def decorator(user_func):
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
        self.ref_cache = weakref.ref(cache)

    def run(self):
        while self.ref_cache():
            cache = self.ref_cache()
            if cache:
                next_expire = cache.cleanup()
                if next_expire is None:
                    time.sleep(self.duration)
                else:
                    time.sleep(next_expire + 1)
            cache = None


class LRUCacheDict:
    def __init__(self, maxsize=128, expiration=5 * 60, cleanup_duration=0, thread_safe=True):
        if maxsize is not None and not isinstance(maxsize, int):
            raise TypeError('Expected maxsize to be an integer or None')
        if expiration is not None and not isinstance(expiration, int):
            raise TypeError('Expected expiration to be an integer or None')
        if cleanup_duration is not None and not isinstance(cleanup_duration, int):
            raise TypeError('Expected cleanup_duration to be an integer or None')
        if cleanup_duration and not thread_safe:
            warnings.warn('Thread cleanup must be run under thread safe, automatically set thread safe!')
            thread_safe = True

        self.maxsize = maxsize
        self.expiration = expiration
        self.thread_safe = thread_safe
        self._cache = OrderedDict()

        if self.thread_safe:
            self._lock = threading.RLock()
        if cleanup_duration:
            ThreadCleanup(self, cleanup_duration).start()

    @_lock_decorator
    def __len__(self):
        return len(self._cache)

    @_lock_decorator
    def __contains__(self, key):
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
        for k in self._cache:
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
        key = repr((args, kwargs)) + '#' + self.user_func.__name__
        res = self._cache.get(key)
        if not res:
            res = self.user_func(*args, **kwargs)
            self._cache[key] = res
        return res
