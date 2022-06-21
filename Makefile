build:
	mv dist/* dist_
	python setup.py bdist_wheel

install:
	pip install dist/*.whl --force-reinstall

