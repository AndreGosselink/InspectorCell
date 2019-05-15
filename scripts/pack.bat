del dist /S /Q /F
del build /S /Q /F

call python setup.py sdist --formats=gztar,zip
call python setup.py bdist_wheel
