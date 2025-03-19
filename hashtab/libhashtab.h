#ifndef LIBHASHTAB_H
#define LIBHASHTAB_H

#include <stddef.h>

/* Basic types for the hash table */
typedef unsigned long hash_T;
typedef unsigned long long_u;

/* Item for a hashtable */
typedef struct hashitem_S {
    long_u  hi_hash;    /* cached hash number of hi_key */
    char    *hi_key;    /* NULL means empty item, HI_KEY_REMOVED means removed item */
} hashitem_T;

/* The address of "hash_removed" is used as a magic number for hi_key to indicate a removed item */
extern char hash_removed;
#define HI_KEY_REMOVED &hash_removed
#define HASHITEM_EMPTY(hi) ((hi)->hi_key == NULL || (hi)->hi_key == &hash_removed)

/* Initial size for a hashtable */
#define HT_INIT_SIZE 16

/* Flags used for ht_flags */
#define HTFLAGS_ERROR   0x01    /* Failed to grow, can't add more items */
#define HTFLAGS_FROZEN  0x02    /* Adding/removing items not allowed */

/* Hash table structure */
typedef struct hashtable_S {
    long_u     ht_mask;        /* mask used for hash value (nr of items in array - 1) */
    long_u     ht_used;        /* number of items used */
    long_u     ht_filled;      /* number of items used + removed */
    int        ht_changed;     /* incremented when adding or removing an item */
    int        ht_locked;      /* counter for hash_lock() */
    int        ht_flags;       /* HTFLAGS_ values */
    hashitem_T *ht_array;      /* points to the array, allocated when not using ht_smallarray */
    hashitem_T ht_smallarray[HT_INIT_SIZE]; /* initial small array */
} hashtab_T;

/* Iterate over all the items in a hash table */
#define FOR_ALL_HASHTAB_ITEMS(ht, hi, todo) \
    for ((hi) = (ht)->ht_array; (todo) > 0; ++(hi))

/* Public API functions */
void hash_init(hashtab_T *ht);
int check_hashtab_frozen(hashtab_T *ht, char *command);
void hash_clear(hashtab_T *ht);
hashitem_T *hash_find(hashtab_T *ht, char *key);
hashitem_T *hash_lookup(hashtab_T *ht, char *key, hash_T hash);
int hash_add(hashtab_T *ht, char *key, char *command);
int hash_add_item(hashtab_T *ht, hashitem_T *hi, char *key, hash_T hash);
int hash_remove(hashtab_T *ht, hashitem_T *hi, char *command);
void hash_lock(hashtab_T *ht);
void hash_unlock(hashtab_T *ht);
hash_T hash_hash(char *key);

#endif /* LIBHASHTAB_H */
