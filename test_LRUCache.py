import time
import pytest
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
    def test_1(self):
        cache = LRUCacheDict(2, 2)
        cache[1] = 1
        time.sleep(1)
        assert cache[1] == 1
        time.sleep(3)
        with pytest.raises(KeyError):
            print(cache[1])
        cache[1] = 1
        cache[2] = 2
        cache[3] = 3
        with pytest.raises(KeyError):
            print(cache[1])
