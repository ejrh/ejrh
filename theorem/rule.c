/*
 * rule.c
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#include "rule.h"
 
#include "tree.h"
#include "lex.h"
#include "table.h"

#include "grammar.tab.h"

#include <stdlib.h>
#include <stdio.h>
#include <sys/stat.h>

static unsigned long int filelength(FILE *file)
{
    struct stat sbuf;
    fstat(fileno(file), &sbuf);
    return sbuf.st_size;
}

int load_rules(TABLE *rules, TABLE *operators, char *filename)
{
    char *data;
    int size, nr;
    
    FILE *file = fopen(filename, "rt");
    if (!file)
        return 0;
    
    size = filelength(file);
    data = malloc(size + 1);
    nr = fread(data, 1, size, file);
    data[nr] = 0;
    
    fclose(file);
    
    PARSER p =
    {
        data,
        data,
        1, 1,
        rules,
        operators,
        NULL
    };
    
    yyparse(&p);
    
    free(data);
    
    return 1;
}

TREE *parse_expression(TABLE *rules, TABLE *operators, char *expr)
{
    PARSER p =
    {
        expr,
        expr,
        1, 1,
        rules,
        operators,
        NULL
    };
    
    yyparse(&p);
    
    return p.expr;
}

int print_rules(TABLE *rules)
{
    int i;
    int num_symbols = 0;
    
    for (i = 0; i < rules->num_things; i++)
    {
        printf("%s: ", rules->names[i]);
        num_symbols += print_tree(rules->things[i]);
        printf(";\n");
    }
    
    return num_symbols;
}

/*
 * Apply a rule to a tree, creating a new tree:
 */
TREE *apply_rule(TREE *target, TREE *point, TREE *rule)
{
    TABLE *matches = make_table((TABLE_DESTRUCTOR_FUNC) delete_tree, (TABLE_COPIER_FUNC) copy_tree);
    int match;
    TREE *ret = NULL;
    TREE *pattern = rule->left, *replacement = rule->right;
    
    match = match_rule(matches, point, pattern);
    
    if (match)
    {
        int i;
        printf("(rule matches)\n");
/*        for (i = 0; i < matches->num_things; i++)
        {
            printf("%s = ", matches->names[i]);
            print_tree(matches->things[i]);
            printf("\n");
        } */
        
        ret = generate_new_tree(matches, target, point, replacement);
    }
    else
    {
        printf("(rule doesn't match)\n");
    }
    
    delete_table(matches);
    
    return ret;
}

int match_rule(TABLE *matches, TREE *target, TREE *pattern)
{
    int l, r;

/*    printf("m_r(");
    print_tree(target);
    printf(", ");
    print_tree(pattern);
    printf(")\n"); */
    
    if (pattern->type->type == NAME)
    {
        TREE *l = table_lookup(matches, pattern->type->name);
        
        if (!l)
        {
            add_to_table(matches, pattern->type->name, target);
            
            return 1;
        }
        else
        {
            return is_same_tree(l, target);
        }
    }

    if (!is_same_symbol(target->type, pattern->type))
        return 0;
    
    l = match_rule(matches, target->left, pattern->left);
    r = match_rule(matches, target->right, pattern->right);
    
    return 1 & l & r;
}

TREE *generate_new_tree(TABLE *matches, TREE *tree, TREE *point, TREE *replacement)
{
    TREE *ret;
    
/*    printf("g_n_t(");
    print_tree(tree);
    printf(")\n"); */
    
    if (tree == NULL)
        return NULL;
    
    if (tree == point)
    {
        ret = generate_replacement_tree(matches, replacement);
    }
    else
    {
        TREE *left, *right;
        left = generate_new_tree(matches, tree->left, point, replacement);
        right = generate_new_tree(matches, tree->right, point, replacement);
        ret = make_tree(copy_symbol(tree->type), left, right);
    }
    
    return ret;
}

TREE *generate_replacement_tree(TABLE *matches, TREE *replacement)
{
    TREE *ret;

/*    printf("g_r_t(");
    print_tree(replacement);
    printf(")\n"); */
    
    if (replacement->type->type == NAME)
    {
        TREE *l = table_lookup(matches, replacement->type->name);
        
//        assert(l != NULL);
        
        ret = copy_tree(l);
    }
    else
    {
        TREE *left, *right;
        left = generate_replacement_tree(matches, replacement->left);
        right = generate_replacement_tree(matches, replacement->right);
        ret = make_tree(copy_symbol(replacement->type), left, right);
    }
    
    return ret;
}
