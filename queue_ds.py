"""
queue_ds.py – Implementación propia de la estructura de datos Queue.
"""


class Node:
    """Nodo individual de la cola enlazada."""

    def __init__(self, data):
        self.data = data
        self.next = None


class Queue:
    """
    Cola FIFO implementada con lista enlazada simple.
    No usa collections.deque ni ninguna estructura estándar de Python.
    """

    def __init__(self):
        self._head = None   # frente de la cola (dequeue aquí)
        self._tail = None   # final de la cola  (enqueue aquí)
        self._size = 0

    # ------------------------------------------------------------------ #
    #  Operaciones principales                                             #
    # ------------------------------------------------------------------ #

    def enqueue(self, item):
        """Agrega un elemento al final de la cola."""
        new_node = Node(item)
        if self._tail is None:          # cola vacía
            self._head = new_node
            self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        self._size += 1

    def dequeue(self):
        """Elimina y devuelve el elemento del frente de la cola."""
        if self.is_empty():
            raise IndexError("dequeue en cola vacía")
        data = self._head.data
        self._head = self._head.next
        if self._head is None:          # la cola quedó vacía
            self._tail = None
        self._size -= 1
        return data

    def peek(self):
        """Devuelve el elemento del frente sin eliminarlo."""
        if self.is_empty():
            raise IndexError("peek en cola vacía")
        return self._head.data

    # ------------------------------------------------------------------ #
    #  Utilidades                                                          #
    # ------------------------------------------------------------------ #

    def is_empty(self):
        return self._size == 0

    def size(self):
        return self._size

    def __len__(self):
        return self._size

    def __repr__(self):
        items = []
        current = self._head
        while current:
            items.append(repr(current.data))
            current = current.next
        return "Queue([" + ", ".join(items) + "])"
