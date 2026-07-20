#ifndef __LINKED_LIST_H__
#define __LINKED_LIST_H__

#include "pico/stdlib.h"

template <class T>
class LinkedListItem
{
public:
  T *Item;
  LinkedListItem<T> *Next;
  LinkedListItem<T> *Prev;

  LinkedListItem(T *item)
  {
    Item = item;
    Prev = nullptr;
    Next = nullptr;
  }
};

template <class T>
class LinkedList
{
public:
  LinkedListItem<T> *Head;
  LinkedListItem<T> *Tail;

  LinkedList()
  {
    Head = nullptr;
    Tail = nullptr;
  }

  void Clear()
  {
    LinkedListItem<T> *next = Head;

    Head = nullptr;
    Tail = nullptr;

    while (next != nullptr)
    {
      LinkedListItem<T> *nextHead = next->Next;
      delete next->Item;
      delete next;
      next = nextHead;
    }
  }

  void Add(LinkedListItem<T> *item, LinkedListItem<T> *after)
  {
    // Are there any items in the list yet?
    if (Head == nullptr)
    {
      // This is the first item, so init list to this item
      Head = item;
      Tail = item;
      return;
    }

    // Adding at head?
    if (after == nullptr)
    {
      // Current 'head' has new 'prev'
      Head->Prev = item;

      // Item 'next' is current head
      item->Next = Head;

      // Set new head to the 'added' item
      Head = item;

      return;
    }

    LinkedListItem<T> *afterNext = after->Next;

    // Insert between after and after->Next
    after->Next = item;
    item->Prev = after;
    item->Next = afterNext;

    // If after was Tail then update Tail to 'added' item
    if (Tail == after)
    {
      // Tail is now the 'added' item
      Tail = item;
    }
    else if (afterNext != nullptr)
    {
      afterNext->Prev = item;
    }
  }
};

template <class T>
class SequencedLinkedListItem : public LinkedListItem<T>
{
public:
  uint16_t Sequence;

  SequencedLinkedListItem(T *item, uint16_t sequence) : LinkedListItem<T>(item)
  {
    Sequence = sequence;
  }
};

template <class T>
class SequenceLinkedList : public LinkedList<T>
{
public:
  SequenceLinkedList() : LinkedList<T>()
  {
  }

  void Add(T *item, uint16_t sequence)
  {
    // Create wrapper for item
    LinkedListItem<T> *linkedListItem = new SequencedLinkedListItem<T>(item, sequence);

    // If no head currently specified then insert at head
    if (this->Head == nullptr)
    {
      LinkedList<T>::Add(linkedListItem, nullptr);
      return;
    }

    SequencedLinkedListItem<T> *next = (SequencedLinkedListItem<T> *)this->Head;
    SequencedLinkedListItem<T> *insertAfter = (SequencedLinkedListItem<T> *)this->Head;

    // Should we insert before head?
    if (sequence < next->Sequence)
    {
      // Insert at head
      LinkedList<T>::Add(linkedListItem, nullptr);
      return;
    }

    // Find the last item with the same or less sequence
    // (ie find where to insert at correct sequence order)
    while (next != nullptr && next->Sequence <= sequence)
    {
      insertAfter = next;
      next = (SequencedLinkedListItem<T> *)next->Next;
    }

    LinkedList<T>::Add(linkedListItem, insertAfter);
  }
};

#endif // __LINKED_LIST_H__