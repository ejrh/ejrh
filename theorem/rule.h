/*
 * rule.h
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#ifndef RULE_H
#define RULE_H

#include "tree.h"
#include "table.h"

extern int load_rules(TABLE *rules, TABLE *operators, char *filename);
extern TREE *parse_expression(TABLE *rules, TABLE *operators, char *expr);

extern int print_rules(TABLE *rules);
extern int print_operators(TABLE *operators);

extern TREE *apply_rule(TREE *target, TREE *point, TREE *rule);
extern int match_rule(TABLE *matches, TREE *target, TREE *rule);
extern TREE *generate_new_tree(TABLE *matches, TREE *tree, TREE *point, TREE *replacement);
extern TREE *generate_replacement_tree(TABLE *matches, TREE *replacement);

#endif
