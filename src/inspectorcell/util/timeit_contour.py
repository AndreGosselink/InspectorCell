import timeit
import IPython as ip

setup = """
from find_contour_toy import get_cv, get_sk, get_testmask

mask1, mask2 = get_testmask()

def cv_runner():
    return get_cv(mask1), get_cv(mask2)

def sk_runner():
    return get_sk(mask1), get_sk(mask2)
"""

cv_perf = timeit.timeit(stmt='cv_runner()', setup=setup, number=10000)
sk_perf = timeit.timeit(stmt='sk_runner()', setup=setup, number=10000)

print('CV2', cv_perf)
print('SkI', sk_perf)
