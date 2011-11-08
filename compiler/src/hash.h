/*
 * hash.h - Defintion of the HASH structure and functions for manipulating it.
 *
 * Copyright (C) 2003, Edmund Horner.
 */

#ifndef HASH_H
#define HASH_H

#define LARGE_HASHTABLE  65521
#define MEDIUM_HASHTABLE 8191
#define SMALL_HASHTABLE  1021
#define TINY_HASHTABLE   127

/**
 * The key type to be used in the hash; indicates how keys are hashed and
 * whether the hash is responsible for managing the keys' memory.
 *   - key_type_direct: a key is exactly 4 bytes long, e.g. an integer
 *     or a pointer (no, this file isn't 64-bit safe!).
 *   - key_type_indirect: a key is a pointer to a block of memory with
 *     length key_len (specified on add_to_hash, etc.), allocated externally.
 *   - key_type_copyable: a key is a pointer of a block of memory with
 *     length key_len, which will be copied when the item is added to the
 *     hash and deallocated when it is removed.
 */
typedef enum KEY_TYPE { key_type_direct, key_type_indirect, key_type_copyable } KEY_TYPE;

/**
 * An entry in the hash.  Intended largely for internal use but also provides
 * direct access to keys and data.  Returned on each iteration of a @a HASH_ITERATOR.
 */
typedef struct HASH_ENTRY
{
    void *key;
    int key_len;
    
    void *data;
} HASH_ENTRY;

/**
 * The hash object.  Should be considered opaque except for the @a num field.
 *
 * Typical usage is:
 *     HASH *h = create_hash(TINY_HASHTABLE, key_type_direct);
 *     add_to_hash(h, ITEM_NAME, strlen(ITEM_NAME), data); 
 *     data2 = get_from_hash(h, ITEM_NAME, strlen(ITEM_NAME)); 
 *     destroy_hash(h);
 */
typedef struct HASH
{
    unsigned int max;
    unsigned int num;
    KEY_TYPE key_type;
    
    HASH_ENTRY *entries;
} HASH;

/** A hash iterator object, used for iterating over all items in the hash table.
 * The order of iteration is undefined and may change if items are inserted
 * in a different order or even between program executions.  Iterating while
 * items are added or removed to hash will result in undefined behaviour.
 *
 * Typical usage (assuming keys are strings):
 *     HASH_ITERATOR iter;
 *     for (hash_iterator(subhash, &iter); hash_iterator_valid(&iter); hash_iterator_next(&iter))
 *     {
 *         HASH_ENTRY *he = iter.entry;
 *         printf("key is %s, data is at address %p\n", he->key, he->data);
 *     }
 */
typedef struct HASH_ITERATOR
{
    HASH *hash;
    int pos;
    HASH_ENTRY *entry;
} HASH_ITERATOR;

/**
 * Create a hash table.
 *
 * @param max Initial size of hash table.
 * @param key_type Type of keys (see @a KEY_TYPE for possible values).
 * @return a new hash table, or NULL if failure (out of memory).
 */
extern HASH *create_hash(int max, KEY_TYPE key_type);

/**
 * Destroy a hash table.  If @a key_type during creation was key_type_copyable,
 * the keys will be deallocated; if they have been previously retreived via 
 * @a find_in_hash or an iterator, then no further dereferences of those
 * particular key pointers should be made.
 *
 * @param hash Hash table to destroy.
 */
extern void destroy_hash(HASH *hash);

/**
 * Find an item in a hash table.  Returns a @a HASH_ENTRY object, containing
 * information about the key and its value.  This means it is possible to
 * look up items where the data is NULL; the returned entry will not be NULL,
 * but it's @a data field will be.
 *
 * @param hash Hash table to look in.
 * @param @key Key to look up.
 * @param @key_len Length of @a key. 
 * @return A @a HASH_ENTRY.
 */
extern HASH_ENTRY *find_in_hash(HASH *hash, void *key, int key_len);

/**
 * Get an item's data from a hash table.  A shorthand for @a find_in_hash
 * where the hash table will not contain NULL values.  See @a find_in_hash
 * for parameter info.
 *
 * @return The data attached to the key, if it exists, or NULL if it doesn't.
 */
extern void *get_from_hash(HASH *hash, void *key, int key_len);

/**
 * Put an item in a hash table.  See @a find_in_hash for additional parameter info.
 *
 * @param data Data to store, typically a pointer to something.
 * @return 1 if the item was added; 0 if the hash table was full (which
 *         probably indicates a bug).
 */
extern int add_to_hash(HASH *hash, void *key, int key_len, void *data);

/**
 * Remove an item from a hash table.  See @a find_in_hash for parameter info.
 *
 * @return 1 if the item was removed; 0 if it did not exist in the first place.
 */
extern int remove_from_hash(HASH *hash, void *key, int key_len);

/**
 * Walk over a hash table, calling a callback function on each item in it.
 * The order is undefined.  If the callback returns non-zero for an item,
 * @a walk_hash will return immediately with that value (and the remaining
 * items will not be visited).
 *
 * The callback takes a pointer to the current item's @a HASH_ENTRY, as
 * well as the @a data pointer passed through from the caller of @a walk_hash.
 *
 * @return the last return value if the function returns nonzero for any item;
 *         0 otherwise. *
 */
extern int walk_hash(HASH *hash,
                     int (* func)(HASH_ENTRY *he, void *data), void *data);

/**
 * Initialise a @a HASH_ITERATOR.  See @a HASH_ITERATOR for example.
 *
 * @param hash The hash table to iterate over.
 * @param iter Pointer to iterator to initialise.
 */
extern void hash_iterator(HASH *hash, HASH_ITERATOR *iter);

/**
 * Is the iterator on a valid entry?  Used to detect when an iterator has
 * iterated past the last item in a hash table.  See @a HASH_ITERATOR for
 * example.
 *
 * @param iter Pointer to iterator to check.
 * @return 1 if the entry is valid; 0 if not (the iterator has exhausted the
 * hash table).
 */
extern int hash_iterator_valid(HASH_ITERATOR *iter);

/**
 * Move the iterator to the next item in a hash table.  See @a HASH_ITERATOR
 * for example.
 *
 * @param iter Pointer to iterator to operate on.
 * @return The hash entry of the item (afer moving to it), or NULL if 
 *         past the last item in the hash table.
 */
extern HASH_ENTRY *hash_iterator_next(HASH_ITERATOR *iter);

#endif
