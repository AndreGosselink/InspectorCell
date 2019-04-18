import pytest

from entity import Entity


def test_unique_id():
    """test if double ids raise error
    and id is always an integer
    """
    
    for i in range(10):
        ent = Entity(i)
        assert isinstance(ent.eid, int)

    for i in (20, 100, 30, 11.11):
        ent = Entity(i)
        assert isinstance(ent.eid, int)

    with pytest.raises(ValueError):
        _ = Entity(9)
