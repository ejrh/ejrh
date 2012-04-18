/*
 * main.c
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#include <stdlib.h>
 
#include "rule.h"

int main(int argc, char *argv[])
{
    TABLE *rules = make_table((TABLE_DESTRUCTOR_FUNC) delete_tree, (TABLE_COPIER_FUNC) copy_tree);
    TABLE *operators = make_table(NULL, NULL);
    
	load_rules(rules, operators, "axioms.tree");
    
    print_rules(rules);
    
    {
        printf("\n\n");
        TREE *t1 = parse_expression(rules, operators, "a & (~b | c)");
        printf("t1 = ");  print_tree(t1);  printf("\n");
        TREE *r = table_lookup(rules, "distrib_and");
        printf("r = ");  print_tree(r);  printf("\n");
        TREE *t2 = apply_rule(t1, t1, r);
        printf("t2 = ");  print_tree(t2);  printf("\n");
    }
    
    delete_table(operators);
    delete_table(rules);

	return 0;
}
