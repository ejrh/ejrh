/*
 * lex.h
 *
 * Copyright (C) 2003, Edmund Horner.
 */

#ifndef LEX_H
#define LEX_H

#include <stdio.h>

#include "symbol.h"
#include "table.h"
#include "tree.h"

#define MAX_NAME_LEN 256

typedef struct PARSER
{
    char *data;
    char *p;
    int line, pos;
    TABLE *table;
    TABLE *operators;
    TREE *expr;
}
PARSER;

extern int yylex(PARSER *parser);

#endif
