#include "libhashtab.h"
#include <stdlib.h>
#include <string.h>

/* Magic value for algorithm that walks through the array */
#define PERTURB_SHIFT 5

/* For removed items */
char hash_removed;

static int hash_may_resize(hashtab_T *ht, int minitems);

/*
 * Initialize an empty hash table.
 */
void hash_init(hashtab_T *ht)
{
    memset(ht, 0, sizeof(hashtab_T));
    ht->ht_array = ht->ht_smallarray;
    ht->ht_mask = HT_INIT_SIZE - 1;
}

/*
 * If "ht->ht_flags" has HTFLAGS_FROZEN then give an error message using
 * "command" and return TRUE.
 */
int check_hashtab_frozen(hashtab_T *ht, char *command)
{
    if ((ht->ht_flags & HTFLAGS_FROZEN) == 0)
        return 0;

    /* Can replace with a callback for error reporting */
    return 1;
}

/*
 * Free the array of a hash table. Does not free the items it contains!
 * If "ht" is not freed then you should call hash_init() next!
 */
void hash_clear(hashtab_T *ht)
{
    if (ht->ht_array != ht->ht_smallarray)
        free(ht->ht_array);
}

/*
 * Find "key" in hashtable "ht". Returns NULL if not found.
 * Returns a pointer to a hashitem.
 */
hashitem_T *hash_find(hashtab_T *ht, char *key)
{
    return hash_lookup(ht, key, hash_hash((char *)key));
}

/*
 * Like hash_find(), but caller computes "hash".
 */
hashitem_T *hash_lookup(hashtab_T *ht, char *key, hash_T hash)
{
    hash_T      perturb;
    hashitem_T  *freeitem;
    hashitem_T  *hi;
    unsigned    idx;

    idx = (unsigned)(hash & ht->ht_mask);
    hi = &ht->ht_array[idx];

    if (hi->hi_key == NULL)
        return hi;
    else if (hi->hi_key == HI_KEY_REMOVED)
        freeitem = hi;
    else if (hi->hi_hash == hash && strcmp(hi->hi_key, key) == 0)
        return hi;
    else
        freeitem = NULL;

    /* Need to search through the table to find the key */
    for (perturb = hash; ; perturb >>= PERTURB_SHIFT)
    {
        idx = (unsigned)((idx << 2U) + idx + perturb + 1U);
        hi = &ht->ht_array[idx & ht->ht_mask];
        if (hi->hi_key == NULL)
            return freeitem == NULL ? hi : freeitem;
        if (hi->hi_key == HI_KEY_REMOVED)
        {
            if (freeitem == NULL)
                freeitem = hi;
        }
        else if (hi->hi_hash == hash && strcmp(hi->hi_key, key) == 0)
            return hi;
    }
}

/*
 * Add item with key "key" to hashtable "ht".
 * Returns FAIL when out of memory or the key is already there.
 */
int hash_add(hashtab_T *ht, char *key, char *command)
{
    hashitem_T  *hi;

    hi = hash_find(ht, key);
    if (!HASHITEM_EMPTY(hi))
        return 0;  /* Failure */

    return hash_add_item(ht, hi, key, hash_hash(key));
}

/*
 * Add item "hi" with key "key" to hashtable "ht".
 * "hi" must have been obtained with hash_find() and point to an empty item.
 * "key" must not be NULL and not empty.
 * Returns FAIL when out of memory.
 */
int hash_add_item(hashtab_T *ht, hashitem_T *hi, char *key, hash_T hash)
{
    /* If resizing failed before and it fails again we can't add an item */
    if (ht->ht_flags & HTFLAGS_ERROR)
        return 0;  /* Failure */

    ++ht->ht_used;
    ++ht->ht_changed;
    if (hi->hi_key == NULL)
        ++ht->ht_filled;
    hi->hi_key = key;
    hi->hi_hash = hash;

    /* When the space gets low may resize the array */
    return hash_may_resize(ht, 0);
}

/*
 * Remove item "hi" from hashtable "ht". "hi" must have been obtained with
 * hash_lookup(). The caller must take care of freeing the item itself.
 * "command" is used for error messages.
 */
int hash_remove(hashtab_T *ht, hashitem_T *hi, char *command)
{
    if (check_hashtab_frozen(ht, command))
        return 0;  /* Failure */
    --ht->ht_used;
    ++ht->ht_changed;
    hi->hi_key = HI_KEY_REMOVED;
    hash_may_resize(ht, 0);
    return 1;  /* Success */
}

/*
 * Lock a hashtable: prevent that ht_array changes.
 * Don't use this when items are to be added!
 * Must call hash_unlock() later.
 */
void hash_lock(hashtab_T *ht)
{
    ++ht->ht_locked;
}

/*
 * Unlock a hashtable: allow ht_array changes again.
 * Table will be resized (shrink) when needed.
 * This must balance a call to hash_lock().
 */
void hash_unlock(hashtab_T *ht)
{
    --ht->ht_locked;
    (void)hash_may_resize(ht, 0);
}

/*
 * Return the hash number for a key.
 */
hash_T hash_hash(char *key)
{
    hash_T  hash;
    char    *p;

    if ((hash = *key) == 0)
        return (hash_T)0;
    p = key + 1;

    while (*p != '\0')
        hash = hash * 101 + *p++;

    return hash;
}

/*
 * Resize a hashtable when it's getting too full.
 * Return FAIL when out of memory.
 */
static int hash_may_resize(hashtab_T *ht, int minitems)
{
    hashitem_T  *temparray;
    hashitem_T  *oldarray, *newarray;
    hashitem_T  *olditem, *newitem;
    unsigned    newi;
    int         todo;
    long_u      newsize;
    long_u      minsize;
    long_u      newmask;
    hash_T      perturb;
    hashitem_T  temparray_buf[HT_INIT_SIZE];

    /* Don't resize a locked table */
    if (ht->ht_locked > 0)
        return 1;  /* Success */

    long_u oldsize = ht->ht_mask + 1;
    if (minitems == 0)
    {
        /* Return quickly for small tables with at least two NULL items */
        if (ht->ht_filled < HT_INIT_SIZE - 1
                && ht->ht_array == ht->ht_smallarray)
            return 1;  /* Success */

        /* Grow or refill when more than 2/3 full */
        if (ht->ht_filled * 3 < oldsize * 2 && ht->ht_used > 0)
            return 1;  /* Success */

        minsize = ht->ht_used * 3 / 2 + 1;
    }
    else
    {
        if (ht->ht_mask + 1 >= (unsigned)minitems)
            return 1;  /* Success */

        /* Use minitems directly */
        minsize = (minitems * 3 + 1) / 2;
    }

    newsize = HT_INIT_SIZE;
    while (newsize < minsize)
    {
        newsize <<= 1;
        if (newsize == 0)
            return 0;  /* Overflow - failure */
    }

    if (newsize == HT_INIT_SIZE)
    {
        /* Use the small array inside the hashdict structure */
        newarray = ht->ht_smallarray;
        if (ht->ht_array == newarray)
        {
            /* Moving from ht_smallarray to ht_smallarray! Happens when there
             * are many removed items. Copy the items to be able to clean up
             * removed items */
            memcpy(temparray_buf, newarray, sizeof(temparray_buf));
            oldarray = temparray_buf;
        }
        else
            oldarray = ht->ht_array;
        memset(ht->ht_smallarray, 0, sizeof(ht->ht_smallarray));
    }
    else
    {
        /* Allocate an array. */
        newarray = calloc(newsize, sizeof(hashitem_T));
        if (newarray == NULL)
        {
            /* Allocation failed, set flag so that we don't try again */
            ht->ht_flags |= HTFLAGS_ERROR;
            return 0;  /* Failure */
        }
        oldarray = ht->ht_array;
    }

    /* Move all the items from the old array to the new one */
    newmask = newsize - 1;
    todo = (int)ht->ht_used;
    for (olditem = oldarray; todo > 0; ++olditem)
    {
        if (!HASHITEM_EMPTY(olditem) && olditem->hi_key != HI_KEY_REMOVED)
        {
            /* Find spot for this item in the new array */
            newi = (unsigned)(olditem->hi_hash & newmask);
            newitem = &newarray[newi];

            if (newitem->hi_key != NULL)
            {
                for (perturb = olditem->hi_hash; ; perturb >>= PERTURB_SHIFT)
                {
                    newi = (unsigned)((newi << 2U) + newi + perturb + 1U);
                    newitem = &newarray[newi & newmask];
                    if (newitem->hi_key == NULL)
                        break;
                }
            }
            *newitem = *olditem;
            --todo;
        }
    }

    /* Free the old array */
    if (oldarray != ht->ht_smallarray)
        free(oldarray);
    ht->ht_array = newarray;
    ht->ht_mask = newmask;
    ht->ht_filled = ht->ht_used;
    ++ht->ht_changed;
    ht->ht_flags &= ~HTFLAGS_ERROR;

    return 1;  /* Success */
}
