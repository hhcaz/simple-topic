import time
from pprint import pprint
from pika_topic import Subscriber


subscriber = Subscriber()
q0 = subscriber.subscribe("demo_topic_0", queue_size=1)
q1 = subscriber.subscribe("demo_topic_0", queue_size=1)
q2 = subscriber.subscribe("demo_topic_1", queue_size=1)

t0 = time.time()
while True:
    t1 = time.time()
    dt = t1 - t0
    
    if dt > 5 and q0 is not None:
        print("[INFO] Unsubscribe queue:", q0)
        # support runtime unsubscribe
        subscriber.unsubscribe_queue(q0)
        q0 = None
    
    if dt > 10:
        break
    
    data = subscriber.get()  # this may return empty dict when 
                             # .get is called more frequently than publisher
    if data:
        pprint(data)
