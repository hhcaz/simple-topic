import pika
import pickle
import threading
from typing import Callable
from functools import partial


class Subscriber(object):
    def __init__(self, conn: pika.BlockingConnection = None):
        self.connection = pika.BlockingConnection() if conn is None else conn
        self.channel = self.connection.channel()
        self.queue_names = []
        self.topic_names = []
        self.callbacks = []
    
    @staticmethod
    def _callback_wrapper(callback: Callable, channel, method, properties, body):
        data = pickle.loads(body)
        return callback(data)
    
    def _attach_queue_to_exchange(self, topic: str, queue_size: int = -1) -> str:
        if queue_size is not None and queue_size > 0:
            arguments = {"x-max-length": queue_size}
        else:
            arguments = None
        
        self.channel.exchange_declare(topic, exchange_type="fanout", auto_delete=False)
        result = self.channel.queue_declare(queue="", exclusive=True, auto_delete=True, 
                                            arguments=arguments)
        queue_name = result.method.queue
        self.channel.queue_bind(
            queue=queue_name,
            exchange=topic
        )
        return queue_name
    
    def _attach_callback_to_queue(self, queue_name: str, callback: Callable = None) -> Callable:
        if callback is not None:
            callback = partial(self._callback_wrapper, callback)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=True
            )
        return callback
    
    def _append(self, topic_name: str, queue_name: str, callback: Callable = None):
        self.topic_names.append(topic_name)
        self.queue_names.append(queue_name)
        self.callbacks.append(callback)
    
    def subscribe(self, topic: str, queue_size: int = -1, callback: Callable = None) -> str:
        """Subscribe to topic

        Args:
            topic (str): topic name
            queue_size (int, optional): 
                queue size, set to -1 to use the default, 
                set to 1 to keep only the latest message
            callback (Callable, optional): 
                callback function when message arrives, 
                only effective when combined with spin. If set to None, 
                then the result can be obtained with non-blocking .get() method
                
                example callback: callback = lambda message: print(message)

        Returns:
            queue_name (str): the auto generated queue name
        """
        queue_name = self._attach_queue_to_exchange(topic, queue_size)
        callback = self._attach_callback_to_queue(queue_name, callback)
        self._append(topic, queue_name, callback)
        return queue_name
    
    def unsubscribe_topic(self, topic_name: str):
        """Unbind all the queues related to the given topic."""
        success = False
        for i in range(len(self.topic_names) - 1, -1, -1):
            if self.topic_names[i] == topic_name:
                self.topic_names.pop(i)
                queue_name = self.queue_names.pop(i)
                self.callbacks.pop(i)
                self.channel.queue_unbind(
                    queue=queue_name,
                    exchange=topic_name
                )
                success = True
        return success
    
    def unsubscribe_queue(self, queue_name: str):
        """Unbind all the topics related to the given queue."""
        success = False
        for i in range(len(self.queue_names) - 1, -1, -1):
            if self.queue_names[i] == queue_name:
                topic_name = self.topic_names.pop(i)
                self.queue_names.pop(i)
                self.callbacks.pop(i)
                self.channel.queue_unbind(
                    queue=queue_name,
                    exchange=topic_name
                )
                success = True
        return success
    
    def spin(self):
        """Blocked, run in loop. Similar as ros spin.

        Raises:
            e: Exception or KeyboardInterrupt
        """
        try:
            self.channel.start_consuming()
        except (Exception, KeyboardInterrupt) as e:
            print("[INFO] Stop consuming.")
            self.channel.stop_consuming()
            raise e
    
    def _get_qdata(self, queue: str):
        method, properties, body = self.channel.basic_get(
            queue=queue,
            auto_ack=True
        )
        
        if method is None:
            return False, None
        else:
            data = pickle.loads(body)
            return True, data
    
    def get(self, queues = None):
        """Fetch data in queues.topic: str, queue_size: int = -1, callback: Callable = None

        Args:
            queues (List[str], str, optional): Query data in queues. If None, query all registered queues. 
                Note queues with callback registered in channel.basic_consume will be ignored as it always returns None

        Returns:
            ret (Dict[str, Any]): query results, returns {queue_name: queue_data}
        """
        if queues is None:
            queues = self.queue_names
        elif isinstance(queues, str):
            queues = [queues]
        
        ret = dict()
        for queue in queues:
            index = self.queue_names.index(queue)
            if self.callbacks[index] is not None:
                # this callback has been registered in channel.basic_consume, 
                # therefore, the related queue always returns None. Here we just skip this
                continue
            ok, data = self._get_qdata(queue)
            if ok:
                ret[queue] = data
        return ret


class SingleSubscriber(object):
    def __init__(
        self, 
        topic: str, 
        queue_size: int = -1, 
        callback: Callable = None, 
        conn: pika.BlockingConnection = None
    ):
        """A subscriber only subscribes one topic with one queue.

        Args:
            topic (str): topic name
            queue_size (int, optional): 
                queue size, set -1 to use the default, 
                set to 1 to keep only the latest message
            callback (Callable, optional): 
                callback function when message arrives, 
                only effective when combined with spin. If set to None, 
                then the result can be obtained with non-blocking .get() method
            conn (pika.BlockingConnection): 
        """
        self._subscriber = Subscriber(conn)
        self._subscriber.subscribe(topic, queue_size, callback)
    
    def get(self):
        """Get data from queue (non-blocking). Do not use with spin.

        Returns
        ------
            ok (bool): whether data is valid
            data (Any): deseralized data
        """
        ok, data = self._subscriber._get_qdata(self._subscriber.queue_names[0])
        return ok, data
    
    def spin(self):
        self._subscriber.spin()


class ThreadedDataGetter(object):
    """Currenly, you'd better not use this :(
    """
    def __init__(self, conn: pika.BlockingConnection = None):
        self._subscriber = Subscriber(conn)
        self._data = dict()
        
        self.thread = threading.Thread(target=self._subscriber.spin)
        self.thread.setDaemon(True)
    
    def data(self):
        return self._data
    
    def start(self):
        self.thread.start()
    
    def _set_data_callback(self, queue_name, data):
        self._data[queue_name] = data
    
    def subscribe(self, topic: str, queue_size: int = -1):
        queue_name = self._subscriber._attach_queue_to_exchange(topic, queue_size)
        callback = partial(self._set_data_callback, queue_name)
        callback = self._subscriber._attach_callback_to_queue(queue_name, callback)
        self._subscriber._append(topic, queue_name, callback)
        return queue_name
    
    def unsubscribe_topic(self, topic_name: str):
        self._subscriber.unsubscribe_topic(topic_name)
    
    def unsubscribe_queue(self, queue_name: str):
        self._subscriber.unsubscribe_queue(queue_name)

