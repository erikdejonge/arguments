#!/usr/bin/env bash
git commit -am "-"
git push
rm -Rf build
rm -Rf dist
rm -Rf *.egg-info
python setup.py build
python setup.py register
python setup.py sdist
python setup.py sdist upload
cd piphomepage
zip console_utils *