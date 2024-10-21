import time
from pprint import pprint
from pika_topic import ThreadedDataGetter


data_getter = ThreadedDataGetter()
q0 = data_getter.subscribe("demo_topic_0")
q1 = data_getter.subscribe("demo_topic_0")
q2 = data_getter.subscribe("demo_topic_1")
data_getter.start()

t0 = time.time()
while True:
    t1 = time.time()
    dt = t1 - t0
    
    # Don't support runtime unsubscribe !!!!
    # if dt > 5 and q0 is not None:
    #     data_getter.unsubscribe_queue(q0)
    #     q0 = None
    
    if dt > 10:
        break
    
    data = data_getter.data()
    pprint(data)

