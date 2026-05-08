from collections import defaultdict
from queue import Queue

class StreamManager:
    def __init__(self):
        self.subscribers = defaultdict(list)
    
    def subscribe(self, id):
        q = Queue()
        self.subscribers[id].append(q)
        return q
    
    def publish(self, id, message):
        if id in self.subscribers:
            for q in self.subscribers[id]:
                q.put(message)
    
    def unsubscribe(self, id, q):
        if id in self.subscribers and q in self.subscribers[id]:
            self.subscribers[id].remove(q)