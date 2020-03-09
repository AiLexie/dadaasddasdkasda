.PHONY: build
.PHONY: build_and_run
.PHONY: build_release
.PHONY: clean
.PHONY: clean_hard

out/*: $(wildcard src/backend/*) out/assets/* out/server_impl/* src/backend/*.py
	mkdir -p out/
	cargo build $(if $(filter true,$(PRODUCTION)),--release)
	cp target/$(if $(filter true,$(PRODUCTION)),release,debug)/server_start out/
	cp target/$(if $(filter true,$(PRODUCTION)),release,debug)/libhyper_py.so out/hyper_py.so
	cp src/frontendmap.json src/statuscodes.json out/

out/server_impl/*: $(wildcard src/backend/*.py)
	mkdir -p out/server_impl/
	-cp src/backend/*.py out/server_impl/
	$(if $(filter true,$(PRODUCTION)),python -m compileall out/*.py)

out/assets/*: $(wildcard src/**/*)
	mkdir -p out/assets/
	-cp src/html/*.html out/assets/
	-cp src/css/*.css out/assets/
	-cp src/media/* out/assets/
	-tsc
	find out/assets/ -mindepth 2 -type f -exec mv -u "{}" out/assets/ ";"
	find out/assets/ -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" ";"
	-babel out/assets/*.js --presets minify --source-maps -d out/assets/

PRODUCTION = false

build: out/*

build_and_run: build
	./debugrun.sh

build_release: PRODUCTION = true
build_release: build

clean:
	rm -rf out

clean_hard: clean
	cargo clean
