test:
	hatch run -- pytest tests
.PHONY: test

bumpversion:
	hatch version minor
.PHONY: bumpversion

build:
	hatch build
.PHONY: build

publish:
	HATCH_INDEX_USER='salotz' hatch -v publish
.PHONY: publish


##

.spack-env: spack.yaml
	spack env create -d .
	spack -e . install

clean:
	rm -rf .spack-env
.PHONY: clean

