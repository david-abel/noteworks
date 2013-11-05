class HeapItem:
    def __init__(self, vertex, depth, parent=None):
        self.vertex = vertex
        self.depth = depth
        self.parent = parent

    def getDepth(self):
        return self.depth

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def __cmp__(self, other):
        '''__cmp__ is supposed to return a negative number if self is
        "smaller" than other, 0 if equal, and a positive number if
        "greater."'''
        return self.depth - other.depth
