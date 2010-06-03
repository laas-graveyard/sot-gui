## hacky Makefile for robotpkg 
all: build

build:
	python setup.py build

install: 
ifndef LOCALBASE
	echo "environement varaible LOCALBASE not defined"
else
	python setup.py install --prefix ${LOCALBASE}
endif

doc:
	cd docs && make html