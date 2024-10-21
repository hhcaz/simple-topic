from pika_topic import Subscriber


subscriber = Subscriber()
subscriber.subscribe("demo_topic_0", queue_size=1, callback=lambda msg: print("queue0 receives:", msg))
subscriber.subscribe("demo_topic_0", queue_size=1, callback=lambda msg: print("queue1 receives:", msg))
subscriber.subscribe("demo_topic_1", queue_size=1, callback=lambda msg: print("queue2 receives:", msg))

subscriber.spin()

