#include <iostream>
#include <format>

#include "memory.h"

size_t memory_start = 0;
size_t memory_end = 0;

int main()
{
	size_t node_header_size = sizeof(memory_node_header_t) - sizeof(void*);

	std::cout << std::format("sizeof(memory_node_header_t): {0}, sizeof(void *): {1}\r\n", sizeof(memory_node_header_t), sizeof(void*));

	size_t memory_size = static_cast<size_t>(256) << 10; // 256 * 1024

	void* memory_addr = (int*)malloc(memory_size);

	memory_init(memory_addr, memory_size);

	std::cout << std::format("Memory total: {0}, avail: {1}, calc avail: {2}\r\n", memory_get_total(), memory_get_available(), memory_get_calculated_available());

	void* p[1024];

	for (int i = 0; i < 1024; i++)
	{
		p[i] = memory_malloc(32);

		std::cout << std::format("Memory total:    {0}, avail: {1}, calc avail: {2}\r\n", memory_get_total(), memory_get_available(), memory_get_calculated_available());
		std::cout << std::format("Memory validate: {0}, avail: {1}\r\n", memory_get_total(), memory_get_total() - (static_cast<unsigned long long>(1024) + node_header_size));
	}

	for (int i = 0; i < 1024; i += 2)
	{
		memory_free(p[i]);
		p[i] = nullptr;

		std::cout << std::format("Memory total:    {0}, avail: {1}, calc avail: {2}\r\n", memory_get_total(), memory_get_available(), memory_get_calculated_available());
		std::cout << std::format("Memory validate: {0}, avail: {1}\r\n", memory_get_total(), memory_get_total() - (static_cast<unsigned long long>(1024) + node_header_size));
	}

	for (int i = 0; i < 1024; i++)
	{
		if (p[i])
		{
			memory_free(p[i]);

			std::cout << std::format("Memory total:    {0}, avail: {1}, calc avail: {2}\r\n", memory_get_total(), memory_get_available(), memory_get_calculated_available());
			std::cout << std::format("Memory validate: {0}, avail: {1}\r\n", memory_get_total(), memory_get_total() - (static_cast<unsigned long long>(1024) + node_header_size));
		}
	}

	std::cout << std::format("Memory total:    {0}, avail: {1}, calc avail: {2}\r\n", memory_get_total(), memory_get_available(), memory_get_calculated_available());
	std::cout << std::format("Memory validate: {0}, avail: {1}\r\n", memory_get_total(), memory_get_available());

	std::cout << std::endl;
}
