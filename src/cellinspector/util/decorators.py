"""implements depreciation warning decorator
"""
import warnings

def depreciated(otherFunc, proxy=True):
    """Generates a depreciation decorator. The _decorator will
    raise an DepreciatedWarning and hint to otherFunc.__name__
    if proxy is True, the call of the decorated function will be
    proxied. Otherwise the wrapped function will be called
    """
    def _depreciationDecorator(depreciatedFunc):
        warn = '{} is depreciated, please use {} instead'
        warn = warn.format(
            depreciatedFunc.__name__,
            otherFunc.__name__,
                )
        def _proxyWrapped(*args, **kwargs):
            warnings.warn(warn)
            return otherFunc(*args, **kwargs)
        def _directWrapped(*args, **kwargs):
            warnings.warn(warn)
            return depreciatedFunc(*args, **kwargs)
        if proxy:
            return _proxyWrapped
        else:
            return _directWrapped
    return _depreciationDecorator
