from typing import Callable

from src.utils.exceptions import InvalidCoinError


def retry(func) -> Callable:
    """

    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        max_times = 3
        for i in range(max_times):
            try:
                res = func(*args, **kwargs)
                return res
            except InvalidCoinError:
                raise
            except Exception as e:
                print(f"第{i+1}次失败：{e}")
    return wrapper