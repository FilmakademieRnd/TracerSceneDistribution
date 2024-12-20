import cProfile
import pstats
from functools import wraps

def QuickProfiler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with cProfile.Profile() as pr:
            result = func(*args, **kwargs)
        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.print_stats()
        return result
    return wrapper