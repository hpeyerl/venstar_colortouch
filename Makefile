# 
# Herb is lazy and can't remember how to do stuff.
#
PYTHON:=python3
PKG:=venstarcolortouch
#
# can't handle the import so force the version.  XXX(hp).
#
#VERSION:=${shell ${PYTHON} src/${PKG}/__init__.py}
VERSION=0.16

all: clean build test

clean:
	rm -rf dist build /tmp/pip-* src/venstarcolortouch.egg-info
	rm -rf venv $HOME/.cache/pip/wheels/8e/22/27/96436ab8e9371fdad01caa13fb9fb0a0e80299ad8ea6b24312
	rm -fr /tmp/venv

build:
	${PYTHON} setup.py sdist bdist_wheel

#
# Test a local install
#
test:
	virtualenv -p ${PYTHON} venv
	#
	# for some reason pip3 on hass won't install latest versions of these.
	# but if I install them in venv we get updated versions.  This is to
	# resolve long_description_content_type issue.
	#
	venv/bin/pip install -U twine wheel setuptools
	venv/bin/pip -v install dist/${PKG}-${VERSION}.tar.gz
	find venv -name "*${PKG}*"

#
# Test an install from pypi test server
# (probably will fail since testpypi doesn't have requests==2.18.4)
#
testpypi:
	cd /tmp ; \
	virtualenv -p ${PYTHON} venv && \
	venv/bin/pip install -i https://testpypi.python.org/pypi ${PKG} && \
	find venv -name "*${PKG}*"
		
upload_test:
	venv/bin/twine upload -r test dist/${PKG}-${VERSION}*

upload_real:
	venv/bin/twine upload -r pypi dist/${PKG}-${VERSION}*

show.%: 
	@echo $*=$($*)
