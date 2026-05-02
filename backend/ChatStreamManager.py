from collections import defaultdict
from queue import Queue

class ChatStreamManager:
    def __init__(self):
        self.subscribers = defaultdict(list)
    
    def subscribe(self, chat_id):
        q = Queue()
        self.subscribers[chat_id].append(q)
        return q
    
    def publish(self, chat_id, message):
        if chat_id in self.subscribers:
            for q in self.subscribers[chat_id]:
                q.put(message)
    
    def unsubscribe(self, chat_id, q):
        if chat_id in self.subscribers and q in self.subscribers[chat_id]:
            self.subscribers[chat_id].remove(q)

stream_manager = ChatStreamManager()