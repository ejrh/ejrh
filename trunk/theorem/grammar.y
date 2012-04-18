/*
 * Grammar for the theorem prover.
 *
 * Copyright (C) 2003, Edmund Horner.
 */

%{
#include "lex.h"
#include "tree.h"
#include "symbol.h"
    
#define YYLEX_PARAM parser
%}

%parse-param {PARSER *parser}
%lex-param {PARSER *parser}

%start file

%union {
    int ch;
    char *name;
    struct TREE *tree;
}

%token <ch> LEX_ERROR

%right <ch> L_PARAN
%left <ch> R_PARAN
%left <ch> COLON
%left <ch> SEMI_COLON

%left <ch> INTERCHANGES
%left <ch> BECOMES

%left <ch> IMPLIES
%left <ch> EQUIVALENT_TO
%nonassoc <ch> CONTRADICTS
%left <ch> OR
%left <ch> AND
%right <ch> NOT
%right <ch> FOR_ALL 
%right <ch> EXISTS
%left <name> NAME
%left <name> BIN_OPERATOR
%left <name> PRE_OPERATOR
%right <name> POST_OPERATOR
%right BINARY POST PRE

%type <tree> expression variable

%%

file:
    /* empty */
    | rule
    | file rule
    | expression
        { parser->expr = $1; }
    ;
    
rule:
    NAME COLON expression INTERCHANGES expression SEMI_COLON
        { TREE *t = make_tree(make_symbol(BECOMES, "BECOMES"), $3, $5);
          add_to_table(parser->table, $1, t);
          t = make_tree(make_symbol(BECOMES, "BECOMES"), $5, $3);
          add_to_table(parser->table, $1, t); }
    | NAME COLON expression BECOMES expression SEMI_COLON
        { TREE *t = make_tree(make_symbol(BECOMES, "BECOMES"), $3, $5);
          add_to_table(parser->table, $1, t); }
    | BINARY NAME SEMI_COLON
        { add_to_table(parser->operators, $2, (void *) BIN_OPERATOR); }
    | POST NAME SEMI_COLON
        { add_to_table(parser->operators, $2, (void *) POST_OPERATOR); }
    | PRE NAME SEMI_COLON
        { add_to_table(parser->operators, $2, (void *) PRE_OPERATOR); }
    | error SEMI_COLON
        { yyerror(parser, "recovering from broken rule"); }
    ;
    
expression:
    expression IMPLIES expression
        { $$ = make_tree(make_symbol(IMPLIES, "IMPLIES"), $1, $3); }
    | expression EQUIVALENT_TO expression
        { $$ = make_tree(make_symbol(EQUIVALENT_TO, "EQUIVALENT_TO"), $1, $3); }
    | expression CONTRADICTS expression
        { $$ = make_tree(make_symbol(CONTRADICTS, "CONTRADICTS"), $1, $3); }
    | expression OR expression
        { $$ = make_tree(make_symbol(OR, "OR"), $1, $3); }
    | expression AND expression
        { $$ = make_tree(make_symbol(AND, "AND"), $1, $3); }
    | NOT expression
        { $$ = make_tree(make_symbol(NOT, "NOT"), NULL, $2); }
    | FOR_ALL variable expression
        { $$ = make_tree(make_symbol(FOR_ALL, "FOR_ALL"), $2, $3); }
    | EXISTS variable expression
        { $$ = make_tree(make_symbol(EXISTS, "EXISTS"), $2, $3); }
    | variable
    | expression BIN_OPERATOR expression
        { $$ = make_tree(make_symbol(BIN_OPERATOR, $2), $1, $3); }
    | PRE_OPERATOR expression
        { $$ = make_tree(make_symbol(PRE_OPERATOR, $1), NULL, $2); }
    | expression POST_OPERATOR
        { $$ = make_tree(make_symbol(POST_OPERATOR, $2), $1, NULL); }
    | L_PARAN expression R_PARAN
        { $$ = $2; }
    ;

variable:
    NAME
        { $$ = make_tree(make_symbol(NAME, $1), NULL, NULL); }

%%
