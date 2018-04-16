.PHONY: test upload clean bootstrap

test:
	(. venv3/bin/activate; \
	tox; \
	)

build: clean
	(. venv3/bin/activate; \
	python3 setup.py sdist build; \
	)

release: _upload tag

_upload: test
	(. venv3/bin/activate; \
	python3 setup.py sdist upload ; \
	make clean; \
	)

tag:
	git tag v`cat bridgy/version.py | grep __version__ | awk -F"=" '{print $$2}' | sed -e 's/^[ \t]*//' | tr -d "'"` && \
	git push --tags

bootstrap3: venv3
	. venv3/bin/activate
	venv3/bin/pip install -e .
	venv3/bin/pip install --upgrade tox
	make clean

venv3:
	virtualenv -p python3 venv3
	venv3/bin/pip install --upgrade pip
	venv3/bin/pip install --upgrade setuptools

bootstrap2: venv2
	. venv2/bin/activate
	venv2/bin/pip install -e .
	venv2/bin/pip install --upgrade tox
	make clean

venv2:
	virtualenv -p python2 venv2
	venv2/bin/pip install --upgrade pip
	venv2/bin/pip install --upgrade setuptools

clean:
	rm -f MANIFEST
	rm -rf build dist