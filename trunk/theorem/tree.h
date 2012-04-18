/*
 * tree.h
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#ifndef TREE_H
#define TREE_H

#include "symbol.h"

typedef struct TREE
{
    SYMBOL *type;
    struct TREE *left;
    struct TREE *right;
} TREE;

extern TREE *make_tree(SYMBOL *type, TREE *left, TREE *right);
extern TREE *combine_trees(TREE *top, TREE *left, TREE *right);
extern TREE *copy_tree(TREE *source);
extern void delete_tree(TREE *tree);
extern int is_same_tree(TREE *a, TREE *b);
extern int print_tree(TREE *tree);

#endif
