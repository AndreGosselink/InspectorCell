"""Controller, bridges between data and view
"""


class Tagging():
    """Wrapper around Tags, use as Mixin Class
    """
    def __init__(self):
        self._tags = set([])
        super().__init__() # so it can be an Mixin

    def addTags(self, tags):
        """Adds tags 

        Parameter
        ---------
        tags : iterable
            iterable of strings, where each string is a tag to be added
        """
        self._tags.update(set(tags))

    def removeTags(self, tags):
        """Remove tags 

        Parameter
        ---------
        tags : iterable
            iterable of strings, where each string is a tag to be removed
        """
        self._tags.difference_update(set(tags))

    @property
    def tags(self):
        return self._tags


class DataManager(Tagging):
    """exchangen object to allow for possible thread safety on shared
    objects/data
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
