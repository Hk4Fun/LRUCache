import time
import pytest
import threading
from LRUCache import lru_cache, LRUCacheDict


@lru_cache(3, 3)
def f(x):
    return x


class TestLRUCache:
    def test_1(self):
        assert f(1) == 1
        time.sleep(1)
        assert f(1) == 1
        time.sleep(3)
        assert f(1) == 1


class TestLRUCacheDict:
    def test_1(self, thread_safe=True):
        cache = LRUCacheDict(2, 2, thread_safe=thread_safe)
        cache[1] = 1
        time.sleep(1)
        assert cache[1] == 1
        time.sleep(3)
        with pytest.raises(KeyError):
            print(cache[1])
        cache[1] = 1
        cache[2] = 2
        cache[3] = 3
        assert cache.size() == 2
        with pytest.raises(KeyError):
            print(cache[1])
        _ = cache[2]
        cache[4] = 4
        with pytest.raises(KeyError):
            print(cache[3])
        time.sleep(2)
        assert cache.size() == 0
        assert 4 not in cache
        assert 2 not in cache

    def test_2(self):
        self.test_1(thread_safe=False)

    def test_3(self):
        with pytest.warns(UserWarning):
            cache = LRUCacheDict(2, 3, cleanup_duration=2, thread_safe=False)
        assert cache.thread_safe is True
        cache[1] = 1
        cache[2] = 2
        cache[3] = 3
        assert cache.size() == 2
        time.sleep(2)
        assert cache.size() == 2
        time.sleep(3)
        assert cache.size() == 0

    def test_4(self):
        time.sleep(2)  # wait for test_3's cleanup thread to exit
        cache = LRUCacheDict(1, 1, 2)
        assert threading.active_count() == 2
        time.sleep(1)
        del cache
        assert threading.active_count() == 2
        time.sleep(2)
        assert threading.active_count() == 1
