#
# Makefile
#
# Copyright (C) 2003, Edmund Horner.
#

CFLAGS = -g -Wall

YACC = bison -d -g -r all

all: theorem

clean:
	rm -f *.o *.tab.h theorem theorem.exe
    
theorem: main.o grammar.tab.o lex.o symbol.o tree.o rule.o table.o
	$(CC) -o theorem main.o grammar.tab.o lex.o symbol.o tree.o rule.o table.o
    
main.o: main.c lex.h
	$(CC) -c main.c
   
grammar.tab.o: grammar.tab.c grammar.tab.h
	$(CC) -c grammar.tab.c
    
grammar.tab.c: grammar.y lex.h
	$(YACC) grammar.y
    
grammar.tab.h: grammar.y lex.h
	$(YACC) grammar.y
    
lex.o: lex.c lex.h grammar.tab.h
	$(CC) -c lex.c

symbol.o: symbol.c symbol.h
	$(CC) -c symbol.c
    
tree.o: tree.c tree.h symbol.h
	$(CC) -c tree.c
    
rule.o: rule.c rule.h tree.h symbol.h
	$(CC) -c rule.c

table.o: table.c table.h tree.h
	$(CC) -c table.c
