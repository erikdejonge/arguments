#!/usr/bin/env bash
pandoc --from=markdown --to=rst --output=README.rst README.md
rm -Rf build
rm -Rf dist
rm -Rf *.egg-info
python3 setup.py build
#python setup.py register
python3 setup.py sdist
python3 setup.py sdist upload
rm README.rst

echo
echo -e "\033[0;32m---------\033[0m"
echo
