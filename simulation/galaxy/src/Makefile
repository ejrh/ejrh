CFLAGS = -g -Wall $(OPT) -I /usr/include/SDL 

OBJ=$(patsubst %.c, %.o, $(wildcard *.c))
HEADERS=galaxy.h

all: galaxy

galaxy: $(OBJ)
	$(CC) -o $@ $(OBJ) $(CFLAGS) -lm -lpng -lSDL -lSDL_ttf 

%.o: %.c $(HEADERS)
	$(CC) -c $< $(CFLAGS)

clean:
	rm -f $(OBJ)

opt:
	$(MAKE) all OPT=-O9

profile:
	$(MAKE) all "OPT=-g -pg"
