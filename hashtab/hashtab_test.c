#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libhashtab.h"

void print_table_stats(hashtab_T *ht) {
    printf("Table statistics:\n");
    printf("  Mask: %lu (size: %lu)\n", ht->ht_mask, ht->ht_mask + 1);
    printf("  Used items: %lu\n", ht->ht_used);
    printf("  Filled slots: %lu\n", ht->ht_filled);
    printf("\n");
}

int main() {
    hashtab_T ht;
    hashitem_T *hi;
    char *items[] = {
        "apple", "banana", "cherry", "date", "elderberry",
        "fig", "grape", "honeydew", "kiwi", "lemon",
        "mango", "nectarine", "orange", "papaya", "quince",
        "raspberry", "strawberry", "tangerine", "watermelon"
    };
    int item_count = sizeof(items) / sizeof(items[0]);
    int i;

    /* Initialize the hash table */
    hash_init(&ht);
    printf("Initialized empty hashtable\n");
    print_table_stats(&ht);

    /* Add items */
    printf("Adding %d items...\n", item_count);
    for (i = 0; i < item_count; i++) {
        if (!hash_add(&ht, items[i], NULL)) {
            printf("Failed to add item: %s\n", items[i]);
        }
    }
    print_table_stats(&ht);

    /* Look up items */
    printf("Looking up items:\n");
    for (i = 0; i < item_count; i++) {
        hi = hash_find(&ht, items[i]);
        if (HASHITEM_EMPTY(hi)) {
            printf("  Failed to find '%s'\n", items[i]);
        } else {
            printf("  Found '%s' with hash %lu\n", hi->hi_key, hi->hi_hash);
        }
    }

    /* Look up a non-existent item */
    printf("\nLooking up a non-existent item:\n");
    hi = hash_find(&ht, "pineapple");
    if (HASHITEM_EMPTY(hi)) {
        printf("  'pineapple' not found (correct)\n");
    } else {
        printf("  Incorrectly found '%s' with hash %lu\n", hi->hi_key, hi->hi_hash);
    }

    /* Remove some items */
    printf("\nRemoving 'apple', 'mango', and 'watermelon'...\n");
    hi = hash_find(&ht, "apple");
    hash_remove(&ht, hi, NULL);
    hi = hash_find(&ht, "mango");
    hash_remove(&ht, hi, NULL);
    hi = hash_find(&ht, "watermelon");
    hash_remove(&ht, hi, NULL);
    print_table_stats(&ht);

    /* Check if removed items are really gone */
    printf("Checking removed items:\n");
    hi = hash_find(&ht, "apple");
    if (HASHITEM_EMPTY(hi)) {
        printf("  'apple' not found (correct)\n");
    } else {
        printf("  Incorrectly found '%s'\n", hi->hi_key);
    }
    
    /* Check if other items still exist */
    hi = hash_find(&ht, "banana");
    if (!HASHITEM_EMPTY(hi)) {
        printf("  'banana' still found (correct)\n");
    } else {
        printf("  Failed to find 'banana'\n");
    }

    /* Clean up */
    hash_clear(&ht);
    printf("\nHash table cleared\n");

    return 0;
}
