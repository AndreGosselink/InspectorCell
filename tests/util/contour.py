import pytest
import numpy as np

from cellinspector.util import EntityContour

AS_CONTOUR = [np.array([[1, 1], [2, 2], [3, 3],], float)]
AS_STRING = '1,1 2,2 3,3'

PARAM_STR = 'name,fmt,cont'

CORRECT = (PARAM_STR, [
    ('string', AS_CONTOUR, AS_STRING),
    ('contour', AS_CONTOUR, AS_CONTOUR),
    ])


@pytest.mark.parametrize(PARAM_STR, CORRECT)
def test_conversionToContour(name, fmt, cont):
    econt = EntityContour()
    setattr(econt, name, fmt)
    
    for curve, oughtCurve in zip(econt.contour, cont):
        assert np.all(curve == oughtCurve)

@pytest.mark.parametrize(PARAM_STR, CORRECT)
def test_conversionFromContour(name, fmt, cont):
    econt = EntityContour()
    econt.contour = cont

    conversion = getattr(econt, name)

    assert conversion == fmt
