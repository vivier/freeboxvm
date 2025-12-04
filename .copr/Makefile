srpm:
	dnf install python3-pip dnf5-plugins python3-setuptools python3-wheel \
		    python3-humanize python3-gobject-devel python3-requests \
		    python3-tqdm python3-websockets
	dnf builddep freeboxvm.spec
	pip install build
	python3 -m build --sdist
	rpmbuild --ta dist/freeboxvm-0.0.1.tar.gz --define "_srcrpmdir $(outdir)"
