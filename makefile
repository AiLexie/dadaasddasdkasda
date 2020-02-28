out/: src/backend/*.py out/assets/
	mkdir -p out/
	cp src/backend/*.py out/

out/assets/: src/* out/assets/*.js
	mkdir -p out/assets/
	-cp src/html/*.html out/assets/
	-cp src/css/*.css out/assets/

out/assets/%.js: src/code/*
	mkdir -p out/assets/
	-cp src/code/*.{js,ts,tsx} out/assets/
	-tsc out/assets/*.{ts,tsx} --experimentalDecorators --sourceMap --jsx "react"
	-babel out/assets/*.js --presets minify --source-maps -d out/assets/

build: out/

clean:
	rm -rf out
