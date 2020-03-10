out/: $(wildcard src/backend/*) out/assets/ out/server_impl/
	mkdir -p out/
	cargo build $(if $(filter true,$(PRODUCTION)),--release)
	cp target/$(if $(filter true,$(PRODUCTION)),release,debug)/server_start out/
	# cp target/$(if $(filter true,$(PRODUCTION)),release,debug)/libhyper_py.so out/hyper_py.so
	cp src/frontendmap.json src/statuscodes.json out/

out/server_impl/: $(wildcard src/backend/*.py)
	mkdir -p out/server_impl/
	-cp src/backend/*.py out/server_impl/
	$(if $(filter true,$(PRODUCTION)),python -m compileall out/*.py)

out/assets/: src/* $(wildcard out/assets/*.js)
	mkdir -p out/assets/
	-cp src/html/*.html out/assets/
	-cp src/css/*.css out/assets/

out/assets/%.js: $(wildcard src/code/*)
	mkdir -p out/assets/
	-cp src/code/*.{js,ts,tsx} out/assets/
	-tsc out/assets/*.{ts,tsx} --experimentalDecorators --sourceMap --jsx "react"
	-babel out/assets/*.js --presets minify --source-maps -d out/assets/

PRODUCTION = true

build: out/

debug: PRODUCTION = false
debug: out/

clean:
	rm -rf out

clean_hard: clean
	cargo clean
