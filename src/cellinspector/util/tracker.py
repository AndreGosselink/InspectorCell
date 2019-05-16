"""Implements ViewState which is effectivly an proxy, that tracks defined calls
"""
import inspect
from collections import OrderedDict as ODict


class CallTracker():
    """Class holding all information of the current viewer State and methods
    to save/load the state

    only last calls to patched functions are stored
    assums static function signature through runtime
    """

    def __init__(self):
        self.registerd_calls = {}

    def get_tracked(self, func):
        """get an wrapper for func
        """
        # define the wrapper function
        def _tracker(*args, **kwargs):
            # get the ret value first
            ret = func(*args, **kwargs)
            # no imidiated error occured, track call
            track_dict = self.registerd_calls[func.__name__]
            for pname, arg in zip(track_dict, args):
                track_dict[pname] = (arg, None)
            
            # keep default value if any
            for key, val in kwargs.items():
                track_dict[key] = (val, track_dict[key][1])

            return ret

        # return the wrapped function
        return _tracker

    def patch(self, func):
        """Monkepatches the bound method func to
        track all calls to it
        """
        trackee = func.__self__
        fname = func.__name__

        sig = inspect.signature(func)
        
        track_dict = ODict()
        for param in sig.parameters.values():
            default = param.default
            if default is inspect._empty:
                default = None
            track_dict[param.name] = None, default

        self.registerd_calls[fname] = track_dict

        tracked_func = self.get_tracked(func)

        setattr(trackee, fname, tracked_func)
