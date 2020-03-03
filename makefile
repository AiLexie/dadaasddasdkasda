.PHONY: build
.PHONY: build_and_run
.PHONY: clean

out/*: out/assets/* src/backend/*.py
	mkdir -p out/
	-cp src/backend/*.py out/
	cp src/frontendmap.json out/

out/assets/*: $(wildcard src/**/*)
	mkdir -p out/assets/
	-cp src/html/*.html out/assets/
	-cp src/css/*.css out/assets/
	-cp src/media/* out/assets/
	-tsc
	find out/assets/ -mindepth 2 -type f -exec mv -u "{}" out/assets/ ";"
	find out/assets/ -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" ";"
	-babel out/assets/*.js --presets minify --source-maps -d out/assets/

build: out/*

build_and_run: build
	./debugrun.sh

clean:
	rm -rf out
