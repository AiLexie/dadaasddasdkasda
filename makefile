out/: out/assets/
	mkdir -p out/
	cp src/backend/*.py out/

out/assets/:
	mkdir -p out/assets/
	cp src/html/*.html out/assets/ 2> /dev/null || :
	cp src/css/*.css out/assets/ 2> /dev/null || :
	tsc src/ts/*.ts --outDir out/assets/ --experimentalDecorators --sourceMap 2> /dev/null || :

build: out/

clean:
	rm -rf out
