#ifndef __MEMORY_H__
#define __MEMORY_H__

// #define PICO

#ifdef PICO
#include "pico/stdlib.h"
#endif

void memory_init(void *start_addr, size_t size);

size_t memory_get_total();
size_t memory_get_available(void);
size_t memory_get_allocated();
size_t memory_get_calculated_available();
size_t memory_get_free_node_count();

/// <summary>
/// Useful for debugging when not compiling for pico (eg debugging / unit testing on desktop)
/// </summary>
#ifndef PICO
typedef struct memory_node_header
{
	struct memory_node_header *next; // Next node in list, nullptr if no next (ie is tail)
	struct memory_node_header *prev; // Prev node in list, nullptr if no prev (ie is head)
	size_t node_block_heap_size;		 // The size of the allocated memory heap block (user memory + list node struct memory)
	char *user_memory_start;				 // The start of the allocated user memory block (at offset 12 in the struct)
} memory_node_header_t;

void memory_free(void *ptr);
void *memory_malloc(size_t size);
void *memory_calloc(size_t count, size_t size);
void *memory_realloc(void *ptr, size_t size);
#endif

#endif // __MEMORY_H__