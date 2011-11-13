CFLAGS = -g -Wall $(OPT)

OBJ=$(patsubst %.c, %.o, $(wildcard *.c))
HEADERS=galaxy.h

all: galaxy

galaxy: $(OBJ)
	$(CC) -o $@ $(OBJ) $(CFLAGS) -lm -lpng

%.o: %.c $(HEADERS)
	$(CC) -c $< $(CFLAGS)

avi:
	avidemux2_cli --load img/*.png --output-format AVI --video-codec FFmpeg4 --save out.avi --quit

clean:
	rm -f $(OBJ)

opt:
	$(MAKE) all OPT=-O9

profile:
	$(MAKE) all "OPT=-g -pg"
