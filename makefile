out/: out/assets/
	mkdir -p out/
	cp src/backend/*.py out/

out/assets/:
	mkdir -p out/assets/
	cp src/html/*.html out/assets/
	cp src/css/*.css out/assets/
	tsc src/ts/*.ts --outDir out/assets/ --experimentalDecorators --sourceMap

build: out/

clean:
	rm -rf out
