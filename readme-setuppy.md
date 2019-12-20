# Some notes on building and uploading PyPI packages

## Building a wheel / sdist
python3 setup.py sdist bdist_wheel

## Checking that twine (pypi tool) passes the built package
twine check dist/*

## Uploading to PyPI
python3 -m twine upload dist/*

