/*
 * symbol.c
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#include "symbol.h"

#include <stdlib.h>

SYMBOL *make_symbol(int type, char *name)
{
    SYMBOL *ret = malloc(sizeof (SYMBOL));
    ret->type = type;
    if (name != NULL)
        strncpy(ret->name, name, MAX_SYMBOL_LENGTH);
    else
        name[0] = 0;
    return ret;
}

SYMBOL *copy_symbol(SYMBOL *source)
{
    SYMBOL *ret = malloc(sizeof (SYMBOL));
    ret->type = source->type;
    strcpy(ret->name, source->name);
    return ret;
}

void delete_symbol(SYMBOL *symbol)
{
    if (symbol == NULL)
        return;
    
    free(symbol);
}

int is_same_symbol(SYMBOL *a, SYMBOL *b)
{
    return a->type == b->type;
}

void print_symbol(SYMBOL *symbol)
{
    if (*symbol->name)
        printf("%s", symbol->name);
    else
        printf("%d", symbol->type);
}
