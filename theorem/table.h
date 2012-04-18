/*
 * table.h
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#ifndef TABLE_H
#define TABLE_H

#define MAX_TABLE_SIZE 1024

typedef void(* TABLE_DESTRUCTOR_FUNC)(void *thing);
typedef void *(* TABLE_COPIER_FUNC)(void *thing);

typedef struct TABLE
{
    TABLE_DESTRUCTOR_FUNC destructor;
    TABLE_COPIER_FUNC copier;
    int num_things;
    char *names[MAX_TABLE_SIZE];
    void *things[MAX_TABLE_SIZE];
} TABLE;

extern TABLE *make_table(TABLE_DESTRUCTOR_FUNC destructor, TABLE_COPIER_FUNC copier);
extern void delete_table(TABLE *table);
extern int add_to_table(TABLE *table, char *name, void *thing);
extern int delete_from_table(TABLE *table, char *name);
extern void *table_lookup(TABLE *table, char *name);

#endif
