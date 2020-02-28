out/: src/backend/*.py out/assets/
	mkdir -p out/
	-cp src/backend/*.py out/

out/assets/: src/* out/assets/*.js
	mkdir -p out/assets/
	-cp src/html/*.html out/assets/
	-cp src/css/*.css out/assets/

out/assets/%.js: src/code/*
	mkdir -p out/assets/
	-tsc
	find out/assets/ -mindepth 2 -type f -exec mv -u "{}" out/assets/ ";"
	find out/assets/ -mindepth 1 -maxdepth 1 -type d -exec rm -r "{}" ";"
	-babel out/assets/*.js --presets minify --source-maps -d out/assets/

build: out/

clean:
	rm -rf out
