from threading import RLock
from typing import Type, Any, T, List
import re


class SingletonMixin:
    """Mixin class to make your class a Singleton class.

    By https://gist.github.com/jhbuhrman as seen here:
    https://gist.github.com/werediver/4396488
    """

    _instance = None
    _rlock = RLock()
    _inside_instance = False

    @classmethod
    def instance(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Get *the* instance of the class, constructed when needed using (kw)args.

        Return the instance of the class. If it did not yet exist, create it
        by calling the "constructor" with whatever arguments and keyword arguments
        provided.

        This routine is thread-safe. It uses the *double-checked locking* design
        pattern ``https://en.wikipedia.org/wiki/Double-checked_locking``_ for this.

        :param args: Used for constructing the instance, when not performed yet.
        :param kwargs: Used for constructing the instance, when not perfored yet.
        :return: An instance of the class
        """
        if cls._instance is not None:
            return cls._instance
        with cls._rlock:
            # re-check, perhaps it was created in the mean time...
            if cls._instance is None:
                cls._inside_instance = True
                try:
                    cls._instance = cls(*args, **kwargs)
                finally:
                    cls._inside_instance = False
        return cls._instance

    def __new__(cls, *args, **kwargs):
        """Raise Exception when not called from the :func:``instance``_ class method.

        This method raises RuntimeError when not called from the instance class method.

        :param args: Arguments eventually passed to :func:``__init__``_.
        :param kwargs: Keyword arguments eventually passed to :func:``__init__``_
        :return: the created instance.
        """
        if cls is SingletonMixin:
            raise TypeError(f"Attempt to instantiate mixin class {cls.__qualname__}")

        if cls._instance is None:
            with cls._rlock:
                if cls._instance is None and cls._inside_instance:
                    return super().__new__(cls, *args, **kwargs)

        raise RuntimeError(
            f"Attempt to create a {cls.__qualname__} instance outside of instance()"
        )


class StrEx(str):
    """String with regex fullmatch comparison

    Dropinreplacements for string used in finding entries
    in multiplex images
    """

    def __init__(self, obj: Any):
        """Generate the regex pattern after default
        initialization

        Parameters
        ----------
        obj : Any
            Object to use in string and to use as pattern
        """
        self._matcher = re.compile(str(obj))

    def __str__(self):
        """Decorating string and __repr__
        """
        return f'StrEx({super().__str__()})'

    def __repr__(self):
        """Decorating string and __repr__
        """
        return f'StrEx({super().__str__()})'

    def __eq__(self, other: Any) -> bool:
        """Overload the __eq__ to do regex fullmatch
        """
        try:
            return self._matcher.fullmatch(other) is not None
        except TypeError:
            return super().__eq__(other)

    def __ne__(self, other: Any) -> bool:
        """Overload the __neq__ to do regex fullmatch
        """
        try:
            return self._matcher.fullmatch(other) is None
        except TypeError:
            return super().__ne__(other)

# TODO combind to dict matcher.
# Wrapper with unifrom interface for finding partial matches
def _match(one: dict, inother: dict) -> bool:
    """Helper to compare metadata dictionaries for partial
    match
    """
    for key in one.keys():
        try:
            if one[key] != inother[key]:
                return False
        except KeyError:
            return False
    return True

def find_matches(metaquery: dict, objects: List[T], single=True) -> List[T]:
    """Helper to compare metadata dictionaries for partial
    match

    Parameters
    ------------
    metaquery : dict
        Dict to be matched

    Returns
    --------
    matches : List[T]
        Subset of objects whitch match metadata

    Raises
    -------
    NameError
        If any object in objects has no `meta` attribute
    """
    ret = []
    for obj in objects:
        if _match(metaquery, obj.meta):
            ret.append(obj)
        if single and ret:
            return ret
    return ret

