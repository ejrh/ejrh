/*
 * tree.c
 *
 * Copyright (C) 2003, Edmund Horner.
 */

#include "tree.h"

#include <stdlib.h>
#include <stdio.h>

TREE *make_tree(SYMBOL *type, TREE *left, TREE *right)
{
    TREE *ret = malloc(sizeof (TREE));
    
    ret->type = type;
    ret->left = left;
    ret->right = right;
    
    return ret;
}

TREE *combine_trees(TREE *top, TREE *left, TREE *right)
{
    top->left = left;
    top->right = right;
    
    return top;
}

TREE *copy_tree(TREE *source)
{
    if (source == NULL)
        return NULL;
    
    TREE *ret = malloc(sizeof (TREE));
    ret->type = copy_symbol(source->type);
    ret->left = copy_tree(source->left);
    ret->right = copy_tree(source->right);
    return ret;
}

void delete_tree(TREE *tree)
{
    if (tree == NULL)
        return;
    
    delete_symbol(tree->type);
    delete_tree(tree->left);
    delete_tree(tree->right);
    free(tree);
}

int is_same_tree(TREE *a, TREE *b)
{
    if (a == NULL && b == NULL)
        return 1;
    
    if (a == NULL || b == NULL)
        return 0;
    
    return (is_same_symbol(a->type, b->type)
        && is_same_tree(a->left, b->left)
        && is_same_tree(a->right, b->right));
}

int print_tree(TREE *tree)
{
    int left_symbols = 0, right_symbols = 0;
    
    if (tree == NULL)
        return 0;
    
    if (tree->left || tree->right)
        printf("(");
    
    if (tree->left)
    {
        left_symbols = print_tree(tree->left);
        printf(" ");
    }
    
    print_symbol(tree->type);
    
    if (tree->right)
    {
        printf(" ");
        right_symbols = print_tree(tree->right);
    }
    
    if (tree->left || tree->right)
        printf(")");
    
    return 1 + left_symbols + right_symbols;
}

/*
int tree_box_width(TREE *tree)
{
    if (tree == NULL)
        return 0;
    
    return BOX_WIDTH + tree_box_width(tree->left) + tree_box_width(tree->right);
}

int tree_box_height(TREE *tree)
{
    if (tree == NULL)
        return 0;
    
    return BOX_WIDTH + MAX(tree_box_width(tree->left), tree_box_width(tree->right));
}
*/
