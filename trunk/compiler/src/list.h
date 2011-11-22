#ifndef LIST_H
#define LIST_H

/**
* @file list.h
 * A list object, holding a sequence of items (which are opaque pointers).  The
 * list will automatically expand as needed when items are added to it.
 */

/** The amount of space initially reserved in a new list. */
#define DEFAULT_LIST_SIZE 10

/** Type of callback used in @a list_foreach.
 *
 * @param item The current list item.
 * @param data Pointer to data passed through from the caller.
 * @return Non-zero stops iterating and returns that value from @a list_foreach.
 */
typedef int (* LIST_FOREACH_CALLBACK) (void *item, void *data);

/** List type, should be opaque except that the @a size field can be useful. */
typedef struct LIST
{
    int size;
    int max;
    void **items;
} LIST;

/**
 * Create a new, empty list.
 *
 * @return A list object.
 */
extern LIST *list_create(void);

/**
 * Destroy a list.  Data pointed to items is not destroyed.
 *
 * @param list The list to detroy.
 */
extern void list_destroy(LIST *list);

/**
 * Append an item to a list.
 *
 * @param list List to append to.
 * @param item Item to append.
 */
extern void list_append(LIST *list, void *item);

/** Insert an item in a list, in a position before an existing item.  Items
 * after that position will be shifted along.  If the @a before item is absent,
 * the new item is not inserted.  If the @a before item occurs more than once
 * in the list, the new item will be inserted before the first occurrence.
 *
 * @param list The list to insert into.
 * @param item The item to insert.
 * @param before An item to search for, and insert a new item in front of.
 */
extern void list_insert_before(LIST *list, void *item, void *before);

/**
 * Remove an item from a list.  If the item is not in the list, the list is
 * unchanged.
 *
 * @param list The list to remove from.
 * @param item The item to remove.
 */
extern void list_remove(LIST *list, void *item);

/**
 * Iterate over a list, calling a callback function for each item.  If the callback
 * returns a non-zero integer, iteration will stop at that item and the callback's
 * return value will be returned.
 *
 * @param list The list to iterate over.
 * @param callback The callback to call; see @a LIST_FOREACH_CALLBACK.
 * @param data A pointer to data to pass through to the callback.
 * @return The last return value from the callback if non-zero; otherwise 0.
 */
extern int list_foreach(LIST *list, LIST_FOREACH_CALLBACK callback, void *data);

#endif
