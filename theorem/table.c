/*
 * table.c
 *
 * Copyright (C) 2003, Edmund Horner.
 */
 
#include "table.h"

#include <stdlib.h>
#include <string.h>

TABLE *make_table(TABLE_DESTRUCTOR_FUNC destructor, TABLE_COPIER_FUNC copier)
{
    TABLE *ret = malloc(sizeof (TABLE));
    
    ret->destructor = destructor;
    ret->copier = copier;
    ret->num_things = 0;
    
    return ret;
}

void delete_table(TABLE *table)
{
    int i;
    
    for (i = 0; i < table->num_things; i++)
    {
        free(table->names[i]);
        if (table->destructor)
            table->destructor(table->things[i]);
    }

    free(table);
}

int add_to_table(TABLE *table, char *name, void *thing)
{
    if (table->num_things >= MAX_TABLE_SIZE)
        return 0;
    
    table->names[table->num_things] = strdup(name);
    if (table->copier)
        table->things[table->num_things] = table->copier(thing);
    else
        table->things[table->num_things] = thing;
    
    table->num_things++;
    
    return 1;
}

int delete_from_table(TABLE *table, char *name)
{
    int i;
    
    for (i = 0; i < table->num_things; i++)
    {
        if (!strcmp(table->names[i], name))
        {
            free(table->names[i]);
            if (table->destructor)
                table->destructor(table->things[i]);
            
            table->names[i] = table->names[table->num_things-1];
            table->things[i] = table->things[table->num_things-1];
            
            table->num_things--;
            return 1;
        }
    }
    
    return 0;
}

void *table_lookup(TABLE *table, char *name)
{
    int i;
    
    for (i = 0; i < table->num_things; i++)
    {
        if (!strcmp(table->names[i], name))
            return table->things[i];
    }
    
    return NULL;
}
