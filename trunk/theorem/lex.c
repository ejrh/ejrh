/*
 * Lexical analyser for the theorem prover.
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#include <ctype.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "lex.h"
#include "grammar.tab.h"

#define MAX(a,b) ((a) > (b) ? (a) : (b))

static int isname (int a)
{
    return isalpha(a) || (a == '_');
}

static int same_token (int a, int b)
{
    if (isname(a) && isname(b))
        return 1;

    if (isname(a) && isdigit(b))
        return 1;

    if (isdigit(a) && isdigit(b))
        return 1;

    if (a == '-' && b == '>')
        return 1;

    if (a == '<' && b == '=')
        return 1;

    if (a == '=' && b == '>')
        return 1;

    if (a == '>' && b == '=')
        return 1;

    return 0;
}

#define NEXT_CHAR do { if (!(*parser->p)) return 0; if (*parser->p == '\n') { parser->line++; parser->pos = 0; } parser->p++; parser->pos++; if (!parser->p) return 0; } while (0);

int yylex(PARSER *parser)
{
    char *q;
    int op_type;
    
    do
    {
        if (*parser->p == '/' && *(parser->p+1) == '*')
        {
            NEXT_CHAR;
            NEXT_CHAR;
            while (*(parser->p-1) != '*' || *parser->p != '/')
            {
                NEXT_CHAR;
            }
            NEXT_CHAR;
        }
        else if (*parser->p == '/' && *(parser->p+1) == '/')
        {
            NEXT_CHAR;
            NEXT_CHAR;
            while (*parser->p != '\n')
            {
                NEXT_CHAR;
            }
            NEXT_CHAR;
        }
        else if (*parser->p == ' ' || *parser->p == '\t' || *parser->p == '\n')
        {
            NEXT_CHAR;
        }
        else
            break;
    }
    while (1);
    
    q = parser->p;
    NEXT_CHAR;
    while (same_token(*(parser->p-1), *parser->p))
        NEXT_CHAR;
    
    yylval.name = malloc(parser->p - q + 1);
    strncpy(yylval.name, q, parser->p - q);
    yylval.name[parser->p - q] = 0;
    
    //printf("[%s]\n", yylval.name);
    
    if (!strcmp(yylval.name, "&"))
    {
        return AND;
    }
    else if (!strcmp(yylval.name, "|"))
    {
        return OR;
    }
    else if (!strcmp(yylval.name, "~"))
    {
        return NOT;
    }
    else if (!strcmp(yylval.name, "->"))
    {
        return IMPLIES;
    }
    else if (!strcmp(yylval.name, "=>"))
    {
        return BECOMES;
    }
    else if (!strcmp(yylval.name, "<=>"))
    {
        return INTERCHANGES;
    }
    else if (!strcmp(yylval.name, "("))
    {
        return L_PARAN;
    }
    else if (!strcmp(yylval.name, ")"))
    {
        return R_PARAN;
    }
    else if (!strcmp(yylval.name, ":"))
    {
        return COLON;
    }
    else if (!strcmp(yylval.name, ";"))
    {
        return SEMI_COLON;
    }
    else if (!strcmp(yylval.name, "binary"))
    {
        return BINARY;
    }
    else if (!strcmp(yylval.name, "pre"))
    {
        return PRE;
    }
    else if (!strcmp(yylval.name, "post"))
    {
        return POST;
    }
    
    op_type = (int) table_lookup(parser->operators, yylval.name);
    if (op_type)
    {
        return op_type;
    }
    
    return NAME;
}

void yyerror(PARSER *parser, char *s)
{
    fprintf(stderr, "%d:%d: %s\n", parser->line, parser->pos, s);
}
