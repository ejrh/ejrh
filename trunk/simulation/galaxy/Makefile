all:
	$(MAKE) -C src "OPT=$(OPT)"
	cp src/galaxy .

avi:
	avidemux2_cli --load img/*.png --output-format AVI --video-codec FFmpeg4 --save out.avi --quit

clean:
	$(MAKE) -C src clean
