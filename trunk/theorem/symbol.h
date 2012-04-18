/*
 * symbol.h
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#ifndef SYMBOL_H
#define SYMBOL_H

#define MAX_SYMBOL_LENGTH 27

typedef struct SYMBOL
{
    int type;
    char name[MAX_SYMBOL_LENGTH+1];
} SYMBOL;

extern SYMBOL *make_symbol(int type, char *name);
extern SYMBOL *copy_symbol(SYMBOL *symbol);
extern void delete_symbol(SYMBOL *symbol);
extern int is_same_symbol(SYMBOL *a, SYMBOL *b);
extern void print_symbol(SYMBOL *symbol);
    
#endif
