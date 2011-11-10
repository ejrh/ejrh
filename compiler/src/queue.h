#ifndef QUEUE_H
#define QUEUE_H

/**
 * @file queue.h
 *
 * A simple FIFO queue object.  Items can be enqueued and dequeued; they are
 * dequeued in the same order that they are enqueued.  An item can occupy
 * several positions on the queue; each time it is dequeued only the first
 * instance of it will be removed.
 *
 * Items are opaque pointers.  The queue object will not attempt to
 * dereference or free items.
 */

/**
 * Internal representation of an item on a queue.  Shouldn't be in the public API.
 **/
typedef struct QUEUE_ITEM
{
    struct QUEUE_ITEM *next;
    void *data;
} QUEUE_ITEM;

/**
 * A queue object.  Should really be opaque.
 */
typedef struct QUEUE
{
    QUEUE_ITEM *head;
    QUEUE_ITEM *tail;
} QUEUE;

/**
 * Create an new empty queue object.
 *
 * @return The new queue.
 */
extern QUEUE *create_queue(void);

/**
 * Destroy a queue.  Does not destroy any items remaining on it.
 *
 * @param queue Queue to destroy.
 */
extern void destroy_queue(QUEUE *queue);

/**
 * Is the queue empty?
 *
 * @param queue Queue to check.
 * @return 1 if it's empty, 0 if it's not.
 */
extern int queue_is_empty(QUEUE *queue);

/**
 * Push/enqueue an item onto the queue.
 *
 * @param queue The queue to push onto.
 * @param data The item to push.
 */
extern void queue_push(QUEUE *queue, void *data);

/**
 * Pop/dequeue an item from a queue.
 *
 * @param queue The queue to pop from.
 * @return The item pointer or NULL if there are no items on the queue.
 */
extern void *queue_pop(QUEUE *queue);

#endif
