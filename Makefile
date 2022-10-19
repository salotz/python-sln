bumpversion:
	hatch version minor
.PHONY: bumpversion

build:
	hatch build
.PHONY: build

publish:
	hatch publish
.PHONY: publish


##

.spack-env: spack.yaml
	spack env create -d .
	spack -e . install

clean:
	rm -rf .spack-env
.PHONY: clean

