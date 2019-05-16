#!/bin/bash

rm -rfv dist
rm -rfv build

python setup.py sdist --formats=gztar,zip bdist_wheel
python setup.py bdist_wheel
