import weakref


class Wrapper(object):

    def __init__(self, key, item):
        self.key = key
        self.item = item



class Cache(dict):

    def __init__(self, max_size=1000):
        self.first = None
        self.last = None
        self.size = 0
        self.max_size = max_size


    def __getitem__(self, key):
        wrapper = dict.__getitem__(self, key)
        self.promote(wrapper)
        return wrapper.item


    def __setitem__(self, key, item):
        try:
            self.__delitem__(key)
        except:
            pass
        wrapper = Wrapper(key, item)
        dict.__setitem__(self, key, wrapper)
        
        wrapper.pred = self.last
        if wrapper.pred is None:
            self.first = wrapper
        else:
            wrapper.pred.next = wrapper
        wrapper.next = None
        self.last = wrapper
        
        self.size += 1
        
        if self.size > self.max_size:
            self.reduce()


    def __delitem__(self, key):
        wrapper = dict.__getitem__(self, key)
        dict.__delitem__(self, key)
        
        if wrapper.pred is None:
            self.first = wrapper.next
        else:
            wrapper.pred.next = wrapper.next
        
        if wrapper.next is None:
            self.last = wrapper.pred
        else:
            wrapper.next.pred = wrapper.pred
        
        self.size -= 1


    def promote(self, wrapper):
        if wrapper.pred is None:
            self.first = wrapper.next
        else:
            wrapper.pred.next = wrapper.next

        if wrapper.next is None:
            self.last = wrapper.pred
        else:
            wrapper.next.pred = wrapper.pred

        wrapper.pred = self.last
        if wrapper.pred is None:
            self.first = wrapper
        else:
            wrapper.pred.next = wrapper
        wrapper.next = None
        self.last = wrapper


    def reduce(self):
        wrapper = self.first
        dict.__delitem__(self, wrapper.key)
        self.first = wrapper.next
        wrapper.next.pred = None

        self.size -= 1
