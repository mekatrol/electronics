#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "memory.h"

// #define MEMORY_USE_ORIG_ALLOC 1
// #define PICO_USE_MALLOC_MUTEX 1

// Align to ' align' boundary
// (((size) + ((align)-1)) & ~((align)-1))
// (((3)    + ((4)-1))     & ~((4)-1))     = 4
// (((4)    + ((4)-1))     & ~((4)-1))     = 4
// (((5)    + ((4)-1))     & ~((4)-1))     = 8
// (((6)    + ((4)-1))     & ~((4)-1))     = 8
// (((7)    + ((4)-1))     & ~((4)-1))     = 8
// (((8)    + ((4)-1))     & ~((4)-1))     = 8
// (((9)    + ((4)-1))     & ~((4)-1))     = 12
static inline size_t memory_align_up(size_t size, size_t align)
{
	return (size_t)(((size) + ((align)-1)) & ~((align)-1));
}

#ifdef PICO
/// @brief A memory block node for tracking a block of memory in the heap.
///        The 'user_memory_start' member overlays the allocated user memory and
///        will contain user data. It should not be used in the memory management code other than to
///        call 'container_of' to get the node address from the user memory pointer.
typedef struct memory_node_header
{
	struct memory_node_header *next; // Next node in list, nullptr if no next (ie is tail)
	struct memory_node_header *prev; // Prev node in list, nullptr if no prev (ie is head)
	size_t node_block_heap_size;		 // The size of the allocated memory heap block (user memory + list node struct memory)
	char *user_memory_start;				 // The start of the allocated user memory block
} memory_node_header_t;

#endif

/// @brief The allocated memory start address
static size_t memory_start_addr;

/// @brief The allocated memory size
static size_t memory_size;

/// @breif The allocated memory end address, this is the first memory address after the allocated addres range,
///        it is not part of the allocatable memory
static size_t memory_end_addr;

/// @brief The head node of the free list, initialise to null
static memory_node_header_t *free_list_head = nullptr;

/// @brief The size of the memory that has been allocated
static size_t memory_allocated = 0;

/// @brief The total size of the memory that is placed in the free heap at startup
static size_t memory_heap_total = 0;

/// @brief Get the total number of bytes allocated
/// @return The total number of bytes allocated
size_t memory_get_allocated()
{
	return memory_allocated;
}

/// @brief Get the total number of bytes in the heap
/// @return The total number of bytes in the heap
size_t memory_get_total()
{
	return memory_size;
}

/// @brief Get the remaining number of bytes available
/// @return the remaining number of bytes available
size_t memory_get_available()
{
	return memory_size - memory_allocated;
}

/// @brief Initialise the free list if not already initialised, allocates all avaialble heap
///        memory to a single node header
static inline void memory_initialise_if_needed()
{
	// Memory initialised?
	if (!free_list_head)
	{
		// Init head pointer to start of free heap
		free_list_head = (memory_node_header_t *)memory_start_addr;

		// This is the first call to assign memory so be need to
		// allocate the entire heap to a block
		free_list_head->next = nullptr;
		free_list_head->prev = nullptr;
		free_list_head->node_block_heap_size = memory_size;

		// Set memory heap total size
		memory_heap_total = free_list_head->node_block_heap_size;
	}
}

/// @brief Initialise meory address range
/// @param start_addr the start address of memory
/// @param end_addr
void memory_init(void *start_addr, size_t size)
{
	memory_start_addr = (size_t)start_addr;
	// NOTE: end address is the first address after the allocated memory block not the
	//       last address of the memory block
	memory_end_addr = memory_start_addr + size;
	memory_size = size;
	memory_initialise_if_needed();
}

/// @brief
/// @return
size_t memory_get_calculated_available()
{
	memory_initialise_if_needed();

	memory_node_header_t *node = (memory_node_header_t *)free_list_head;

	size_t bytes_available = 0;

	while (node != nullptr)
	{
		bytes_available += node->node_block_heap_size;

		node = node->next;
	}

	return bytes_available;
}

/// @brief
/// @return
size_t memory_get_free_node_count()
{
	memory_initialise_if_needed();

	memory_node_header_t *node = (memory_node_header_t *)free_list_head;

	size_t free_node_count = 0;

	while (node != nullptr)
	{
		free_node_count++;
		node = node->next;
	}

	return free_node_count;
}

/// @brief Get size of the node header not including the user_memory_start pointer.
/// @return The size of the memory consumed by the node header (not including user_memory_start)
static inline size_t memory_node_header_size()
{
	size_t sizeof_user_memory_start = memory_align_up(sizeof(char *), sizeof(void *));
	size_t sizeof_header = memory_align_up(sizeof(memory_node_header_t), sizeof(void *));
	size_t size = sizeof_header - sizeof_user_memory_start;

	return size;
}

/// @brief Return the maximum of size and min_block_size, which is the minimum memory size required to allocate
/// @param size desired size to allocate
/// @return the minimum size that should be allocated
static inline size_t memory_min_allocatable_size(size_t size)
{
	// Get the minimum number of bytes that a node block can be contain for size
	size_t min_block_size = memory_node_header_size() + sizeof(void *);
	return size > min_block_size ? size : min_block_size;
}

/// @brief Determine if the node can be split into two nodes of size and remainder
/// @param node the node to split
/// @param size the new size of the node
/// @return true if can be split, false if too small to split
static inline bool memory_can_split_node(memory_node_header_t *node, size_t size)
{
	size_t remainder_size = memory_align_up(node->node_block_heap_size - static_cast<size_t>(size), sizeof(void *));
	size_t min_allocatable_size = memory_min_allocatable_size(0);
	return remainder_size >= min_allocatable_size;
}

/// @brief A helper to get the node header from the user memory pointer
/// @param ptr The user memoey pointer
/// @return The node for the user memory pointer
static inline memory_node_header_t *memory_get_node(void *ptr)
{
	size_t address = reinterpret_cast<size_t>(ptr);
	return (memory_node_header_t *)(address - (sizeof(memory_node_header_t) - sizeof(void *)));
}

/// @brief Get the first node header in the free list whose memory is after specified node memory
/// @param node The node to find a following free node for
/// @return The first free node after node, nullptr if no nodes after the specified node
static inline memory_node_header_t *memory_get_node_following_free_node(memory_node_header_t *node)
{
	// Start at head
	memory_node_header_t *next_node = (memory_node_header_t *)free_list_head;

	do
	{
		// Is next_node after node?
		if (next_node > node)
		{
			// This function assumes free list nodes are ordered in memory order
			// so we can break on the first occurence of a next_node > node
			break;
		}

		// Move to next node
		next_node = next_node->next;
	} while (next_node != nullptr);

	// Will be null if no nodes in free list are after 'node'
	return next_node;
}

/// @brief Get the last node header in the free list whose memory is before specified node memory
/// @param node The node to find a prior free node for
/// @return The last free node before node, nullptr if no nodes before the specified node
static inline memory_node_header_t *memory_get_node_prior_free_node(memory_node_header_t *node)
{
	// Start at head
	memory_node_header_t *next_node = (memory_node_header_t *)free_list_head;

	// Start will null prior node
	memory_node_header_t *prior_node = nullptr;

	while (next_node != nullptr && next_node < node)
	{
		// So far most prior node
		prior_node = next_node;

		// Move to next node
		next_node = next_node->next;
	}

	// Will be null if no nodes in free list are priot to 'node'
	return prior_node;
}

/// @brief Split a node into two chunks where the node size will be 'size' and the new node
///        size will be (node->node_block_heap_size - size), assumption is that size has already had memory_align_up applied
/// @param node the node to split into two
/// @param new_size the new size (header + user memory) for existing node,
///                 the new node will have a size of node->node_block_heap_size - new_size
/// @return the new node that was created when the orginal node was split, nullptr if could not be split
static inline memory_node_header_t *memory_split_node(memory_node_header_t *node, size_t new_size)
{
	if (!memory_can_split_node(node, new_size))
	{
		return nullptr;
	}

	// The new node is created in the memory block of the node being split
	memory_node_header_t *new_node = (memory_node_header_t *)(reinterpret_cast<unsigned char *>(node) + new_size);

	// Insert between node and node->next
	new_node->prev = node;
	new_node->next = node->next;
	node->next = new_node;

	if (new_node->next != nullptr)
	{
		new_node->next->prev = new_node;
	}

	// Set new node size
	new_node->node_block_heap_size = node->node_block_heap_size - new_size;

	// Adjust existing node size
	node->node_block_heap_size = new_size;

	// Return the inserted node
	return new_node;
}

/// @brief Remove the node from the linked list, set:
///        node->prev->next to node->next (if node->prev not null)
///        node->next->prev to node->prev (if node->next not null)
/// @param node the node to removed from the list
static inline void memory_remove_node(memory_node_header_t *node)
{
	// Point prev at next
	if (node->prev)
	{
		node->prev->next = node->next;
	}

	// Point next at prev
	if (node->next)
	{
		node->next->prev = node->prev;
	}

	// Clear next and prev for this node
	node->next = nullptr;
	node->prev = nullptr;
}

/// @brief Remove the node from the linked list, set:
///        node->prev->next to node->next (if node->prev not null)
///        node->next->prev to node->prev (if node->next not null)
/// @param node the node to remove from the list
static inline void memory_insert_node(memory_node_header_t *node, memory_node_header_t *node_after)
{
	node->next = nullptr;
	node->prev = node_after;

	if (node_after != nullptr)
	{
		// Insert node between node_after and node_after->next
		node->next = node_after->next;
		node_after->next = node;

		// If node_after->next then set its prev value
		if (node_after->next != nullptr)
		{
			node_after->next->prev = node;
		}
	}

	// If the node is before head node then move head node
	if (node < free_list_head)
	{
		free_list_head = node;
	}
}

/// @brief Defrag the free heap, will join nodes where they are consecutive in memory (one immediatley follows the other in memory)
static inline void memory_free_defrag()
{
	// Get pointer to first two nodes
	memory_node_header_t *node = (memory_node_header_t *)free_list_head;
	memory_node_header_t *next_node = free_list_head->next;

	while (next_node != nullptr)
	{

		// If they are consecutive blocks then merge
		if ((reinterpret_cast<unsigned char *>(node) + node->node_block_heap_size) ==
				reinterpret_cast<unsigned char *>(next_node))
		{
			// Update node to consume next_node
			node->node_block_heap_size = node->node_block_heap_size + next_node->node_block_heap_size;
			node->next = next_node->next;

			// Move next node to the node currently folloing next_node
			next_node = next_node->next;
		}
		else
		{
			// Move to next two nodes
			node = next_node;
			next_node = node->next;
		}
	}
}

/// @brief Standard free method
/// @param ptr user memory to place back i nthe free list
#ifdef PICO
static inline
#endif
		void
		memory_free(void *ptr)
{
	// Do nothing for null
	if (!ptr)
	{
		return;
	}

	// Get the node for this memory pointer
	memory_node_header_t *node = memory_get_node(ptr);

	// Update the allocated memory
	memory_allocated -= node->node_block_heap_size;

	// If we have depleted free nodes then just use this node
	// as the onlyfree node
	if (free_list_head == (memory_node_header_t *)&memory_end_addr)
	{
		free_list_head = node;
		node->prev = nullptr;
		node->next = nullptr;
		return;
	}

	// Find node with memory prior to this node
	memory_node_header_t *after_node = nullptr;
	memory_node_header_t *next_node = (memory_node_header_t *)free_list_head;

	do
	{
		// Is next_node between after_node && node?
		if (next_node < node && (after_node == nullptr || after_node < next_node))
		{
			// Update after_node to this node
			after_node = next_node;
		}

		next_node = next_node->next;
	} while (next_node != nullptr);

	// after_node can be null if the node is before the current head node
	// so insert at head
	if (after_node == nullptr)
	{
		memory_node_header_t *head = (memory_node_header_t *)free_list_head;

		node->prev = nullptr;
		node->next = head;
		if (head != nullptr)
		{
			head->prev = node;
		}
		free_list_head = node;
	}
	else
	{
		memory_insert_node(node, after_node);
	}

	// Run defrag routine upon freeing memory
	memory_free_defrag();
}

/// @brief Standard malloc method
/// @param size The size of user memory to allocate
/// @return user memory for allocation, or nullptr if not enough memory available to allocate
#ifdef PICO
static inline
#endif
		void *
		memory_malloc(size_t size)
{
	memory_initialise_if_needed();

	if (size <= 0)
	{
		return NULL;
	}

	// Get min size and align the size to a boundary sizeof(void *)
	size_t align = sizeof(void *);
	size_t user_align_size = memory_align_up(size, align);
	size_t min_size = memory_min_allocatable_size(user_align_size + memory_node_header_size());

	// Look for first free memory block that can contain size, try and find the smallest available
	// to reduce fragmentation (if latge blocks are continually split)
	size_t smallest_free_block_size = ~0; // Start with max value
	memory_node_header_t *free_node = nullptr;
	memory_node_header_t *next_node = (memory_node_header_t *)free_list_head;

	do
	{
		// Is the need node big enough and smaller than the smallest free node so far
		if (next_node->node_block_heap_size >= min_size && next_node->node_block_heap_size < smallest_free_block_size)
		{
			// This is the smallest free block so far
			free_node = next_node;
			smallest_free_block_size = next_node->node_block_heap_size;
		}
		next_node = next_node->next;
	} while (next_node != nullptr);

	// We were unable to allocate any memory
	if (free_node == nullptr)
	{
		return nullptr;
	}

	// We have a free node, so lets first see if it is large enough to split
	// into a smaller block
	// Split free node into two nodes with free_node size of min_size, and the new node size of node->node_block_heap_size - min_size
	memory_node_header_t *new_node = memory_split_node(free_node, min_size);

	if (free_node == free_list_head)
	{
		if (new_node)
		{
			free_list_head = new_node;
		}
		else
		{
			// We have depleted all memory, set free_list_head to memory_end
			// just to indicate we are out of free nodes
			free_list_head = (memory_node_header_t *)&memory_end_addr;
		}
	}

	// Remove the free node from the free memory heap
	memory_remove_node(free_node);

	// Update the allocated memory, use the actual node allocated memory size
	// as more memory than requested may have been allocated (eg last free memory)
	memory_allocated += free_node->node_block_heap_size;

	// Return the address of the user memory (the memort pointer)
	return &free_node->user_memory_start;
}

/// @brief Standard calloc method
/// @param count The number of elements to allocate
/// @param size The size of one element
/// @return user memory for allocation, or nullptr if not enough memory available to allocate
#ifdef PICO
static inline
#endif
		void *
		memory_calloc(size_t count, size_t size)
{
	// Determine memory allocation size
	size_t full_size = count * size;

	// Allocate the full amount of memory
	void *p = malloc(full_size);

	// Make sure that malloc successfully assigned the memory
	if (!p)
	{
		return p;
	}

	// Calloc clears the assigned memory
	memset(p, 0, count * size);

	return p;
}

/// @brief Standard realloc method
/// @param ptr The existing memory to try and reallocate
/// @param size The new memory size being requested
/// @return user memory for allocation, or nullptr if not enough memory available to reallocate
#ifdef PICO
static inline
#endif
		void *
		memory_realloc(void *ptr, size_t size)
{
	// Get the node for the existing memory pointer
	memory_node_header_t *node = memory_get_node(ptr);

	// Get the new size (including node header)
	size_t new_size = memory_align_up(size, sizeof(void *)) + memory_node_header_size();

	if (new_size < node->node_block_heap_size)
	{

		memory_node_header_t *free_node = memory_split_node(node, new_size);

		// We are reducing size so check if was big enough to split
		if (free_node)
		{
			// Get the free list node to insert after
			memory_node_header_t *insert_after = memory_get_node_prior_free_node(free_node);

			// Block was big enough to split, so add the block that was plit off orginal node to free list
			memory_insert_node(node, insert_after);
		}

		// Return the orginal that has been shrunk
		return ptr;
	}

	// First we try to grow the current allocation if there is memory available to grow

	// Allocate a new set of memory
	void *p = malloc(size);

	// Make sure that malloc successfully assigned the memory
	if (!p)
	{
		return p;
	}

	// Copy the old allocation to the new allocation
	memcpy(p, node->user_memory_start, node->node_block_heap_size - memory_node_header_size());

	// Free the old allocation
	free(ptr);

	// Return the new allocation
	return p;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#if PICO_USE_MALLOC_MUTEX
#include "pico/mutex.h"
auto_init_mutex(malloc_mutex);
#endif

extern "C" void *__real_malloc(size_t size);
extern "C" void *__real_calloc(size_t count, size_t size);
extern "C" void *__real_realloc(void *mem, size_t size);
extern "C" void __real_free(void *mem);

extern "C" void *__wrap_malloc(size_t size)
{
#if PICO_USE_MALLOC_MUTEX
	mutex_enter_blocking(&malloc_mutex);
#endif

#ifdef MEMORY_USE_ORIG_ALLOC
	void *rc = __real_malloc(size);
#else
	void *rc = memory_malloc(size);
#endif
#if PICO_USE_MALLOC_MUTEX
	mutex_exit(&malloc_mutex);
#endif
	return rc;
}

extern "C" void *__wrap_calloc(size_t count, size_t size)
{
#if PICO_USE_MALLOC_MUTEX
	mutex_enter_blocking(&malloc_mutex);
#endif
#ifdef MEMORY_USE_ORIG_ALLOC
	void *rc = __real_calloc(count, size);
#else
	void *rc = memory_calloc(count, size);
#endif
#if PICO_USE_MALLOC_MUTEX
	mutex_exit(&malloc_mutex);
#endif
	return rc;
}

extern "C" void *__wrap_realloc(void *mem, size_t size)
{
#if PICO_USE_MALLOC_MUTEX
	mutex_enter_blocking(&malloc_mutex);
#endif
#ifdef MEMORY_USE_ORIG_ALLOC
	void *rc = __real_realloc(mem, size);
#else
	void *rc = memory_realloc(mem, size);
#endif
#if PICO_USE_MALLOC_MUTEX
	mutex_exit(&malloc_mutex);
#endif
	return rc;
}

extern "C" void __wrap_free(void *ptr)
{
#if PICO_USE_MALLOC_MUTEX
	mutex_enter_blocking(&malloc_mutex);
#endif
#ifdef MEMORY_USE_ORIG_ALLOC
	__real_free(ptr);
#else
	memory_free(ptr);
#endif
#if PICO_USE_MALLOC_MUTEX
	mutex_exit(&malloc_mutex);
#endif
}
