import pika
import pickle


class Publisher(object):
    def __init__(self, topic: str, conn: pika.BlockingConnection = None):
        self.topic = topic
        self.connection = pika.BlockingConnection() if conn is None else conn
        self.channel = self.connection.channel()
        self.channel.exchange_declare(topic, exchange_type="fanout", auto_delete=False)

    def publish(self, obj):
        bdata = pickle.dumps(obj)
        self.channel.basic_publish(
            exchange=self.topic,
            routing_key="",
            body=bdata
        )

