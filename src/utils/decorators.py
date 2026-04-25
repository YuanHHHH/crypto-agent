from typing import Callable

from src.utils.exceptions import InvalidCoinError


def retry(func):
    def wrapper(*args, **kwargs):
        import traceback
        print(f"[RETRY] calling {func.__name__}, args={args}, kwargs={kwargs}")
        try:
            res = func(*args, **kwargs)
            print(f"[RETRY] {func.__name__} returned: {str(res)[:200]}")
            return res
        except Exception as e:
            print(f"[RETRY] {func.__name__} raised: {e}")
            traceback.print_exc()
            raise
    return wrapper