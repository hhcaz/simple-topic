# Pika Topic

This is a toy implementation of a topic-based pub/sub IPC (using [RabbitMQ](https://www.rabbitmq.com/)) as an alternative of [ROS](https://www.ros.org/)'s Publisher/Subscriber.

## Dependencies

* rabbitmq-server
  
  You can skip this step if you want to only publish/subscribe to a topic host on a remote machine.
  ```bash
  sudo apt install erlang rabbitmq-server
  ```
* [pika](https://github.com/pika/pika) python package
  ```python
  pip install pika
  ```


## Usage
### 1. Setup
* Launch the rabbitmq-server: 
  ```
  sudo service rabbitmq-server restart
  ```
  You can check the status of rabbitmq-server via:
  ```
  sudo systemctl status rabbitmq-server
  ```
* Then enable rabbitmq_management:
  ```
  sudo rabbitmq-plugins enable rabbitmq_management
  ```

### 2. Example Publisher
See `examples/demo_publisher.py`
```python
import numpy as np
from pika_topic import Publisher, Rate

publisher0 = Publisher("demo_topic_0")
publisher1 = Publisher("demo_topic_1")
rate = Rate(50)  # Hz

print("[INFO] Start publishing...")
frame_id = 0
while True:
    publisher0.publish([f"frame {frame_id} of publisher 0:", 
                        np.random.rand(3)])
    publisher1.publish([f"frame {frame_id} of publisher 1:", 
                        np.random.rand(3)])
    frame_id += 1
    rate.sleep()

# run this with: python -m examples.demo_publisher
```
The above script uses two publisher to publish random numpy arrays at the rate at 50Hz.


### 3. Example Subscriber
See `examples/demo_subscriber_blocking.py`
```python
from pika_topic import Subscriber

subscriber = Subscriber()

subscriber.subscribe(
    "demo_topic_0", 
    queue_size=1, 
    callback=lambda msg: print("queue0 receives:", msg)
)
subscriber.subscribe(
    "demo_topic_0", 
    queue_size=1, 
    callback=lambda msg: print("queue1 receives:", msg)
)
subscriber.subscribe(
    "demo_topic_1", 
    queue_size=1, 
    callback=lambda msg: print("queue2 receives:", msg)
)

subscriber.spin()

# run this with: python -m examples.demo_subscriber_blocking
```
The above script registers two callbacks on topic `demo_topic_0` and one callback on topic `demo_topic_1`. Each callback receives data from the unique queue.

### 4. More Examples
* See `examples/demo_subscriber_non_blocking.py` for running subscriber without spin and get latest data at any time you want.
* See `examples/demo_subscriber_threading.py` for running subscriber's spin in background thread and fetch data in the main thread (not recommanded).


### 5. Some Utilities
* List existing exchanges (topics) via rabbitmq utils:
  ```
  sudo rabbitmqctl list_exchanges
  ```
* List existing queues via rabbitmq utils:
  ```
  sudo rabbitmqctl list_queues
  ```
* Delete exsiting exchanges (topics) via `pika_topic.del`:
  
  Show help on how to use:
  ```
  >> python -m pika_topic.del -h

  usage: del.py [-h] [-n NAME] [-u USER] [-v VHOST] [-y] [-ip IP]
                [-mp MANAGE_PORT] [-pp PIKA_PORT] [-a AUTH]

  options:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  re pattern to filter name of queried exchanges
    -u USER, --user USER  re pattern to filter user of queried exchanges
    -v VHOST, --vhost VHOST
                          re pattern to filter vhost of queried exchanges
    -y, --yes             set true to skip the deletion confirm
    -ip IP, --ip IP       address of server hosting rabbitmq-server and
                          rabbitmq_management
    -mp MANAGE_PORT, --manage_port MANAGE_PORT
                          port of rabbitmq_management, default is 15672
    -pp PIKA_PORT, --pika_port PIKA_PORT
                          address of pika server, default is 5672
    -a AUTH, --auth AUTH  auth to establish connection to host, format is
                          username@passwd, default is guest@guest
  ```
  For example, we can delete the topic `demo_topic_0` allocated by previous publisher demo via:
  ```
  python -m pika_topic.del -n demo_topic_0
  ```
  We could also delete all the topics allocated by `guest` user via:
  ```
  python -m pika_topic.del -u guest
  ```

* Echo message from existing exchange (topic) via `pika_topic.echo`:
  
  Show help on how to use:
  ```
  >> python -m pika_topic.echo -h

  usage: echo.py [-h] [-n NAME] [-u USER] [-v VHOST] [-p PRECISION]
                 [-ip IP] [-mp MANAGE_PORT] [-pp PIKA_PORT] [-a AUTH]

  usage: echo.py [-h] [-n NAME] [-u USER] [-v VHOST] [-p PRECISION]
                 [-ip IP] [-mp MANAGE_PORT] [-pp PIKA_PORT] [-a AUTH]

  options:
    -h, --help            show this help message and exit
    -n NAME, --name NAME  re pattern to filter name of queried exchanges
    -u USER, --user USER  re pattern to filter user of queried exchanges
    -v VHOST, --vhost VHOST
                          re pattern to filter vhost of queried exchanges
    -p PRECISION, --precision PRECISION
                          displayed precision of numpy arrays in message,
                          default is 3
    -ip IP, --ip IP       address of server hosting rabbitmq-server and
                          rabbitmq_management, default is localhost
    -mp MANAGE_PORT, --manage_port MANAGE_PORT
                          port of rabbitmq_management, default is 15672
    -pp PIKA_PORT, --pika_port PIKA_PORT
                          address of pika server, default is 5672
    -a AUTH, --auth AUTH  auth to establish connection to host, format is
                          username@passwd, default is guest@guest
  ```
  For example, we can show the message from topic `demo_topic_0` via:
  ```
  python -m pika_topic.echo -n demo_topic_0
  ```
  If the previous example publisher is still running, you would see this in your terminal:
  ```
  [INFO] Counts: 170
  [INFO] FPS: 50.017830360522325
  [INFO] Data: 
  ['frame 425754 of publisher 0:', array([0.27 , 0.477, 0.384])]
  -------------------------------------------------------------
  [INFO] Counts: 171
  [INFO] FPS: 49.946736400001555
  [INFO] Data: 
  ['frame 425755 of publisher 0:', array([0.763, 0.563, 0.692])]
  -------------------------------------------------------------
  [INFO] Counts: 172
  [INFO] FPS: 50.011179038031045
  [INFO] Data: 
  ['frame 425756 of publisher 0:', array([0.299, 0.072, 0.664])]
  ```

### 6. Publish/Subscribe to Remote Topics
Suppose we have three machines:
* A: ip = 192.168.3.5, runing a subscriber.
* B: ip = 192.168.3.6, running a publisher.
* C: ip = 192.168.3.7, running a rabbitmq-server on port 5672, and rabbitmq_management on port 15672. The user of machine C is `Cassie`, the rabbitmq-server runs with default user `guest`.

B want to publish message to topic "demo_remote_topic", and A want to subscribe to topic "demo_remote_topic". 

Using default `guest` user on C only accepts requests from C's `localhost`. To enable publishing/subscribing to remote topics, we could: 

#### Option 1: Using SSH Local Port Forward
* on machine A, we runs:
  ```
  ssh -fCNL 5672:localhost:5672 Cassie@192.168.3.7
  ssh -fCNL 15672:localhost:15672 Cassie@192.168.3.7
  ```
* on machine B, we runs:
  ```
  ssh -fCNL 5672:localhost:5672 Cassie@192.168.3.7
  ssh -fCNL 15672:localhost:15672 Cassie@192.168.3.7
  ```
Then we could run previous examples as usual, as the ssh would transmit the traffic to C's localhost which would be accepted by `guest` user.

#### Option 2: Create a New User for RabbitMQ Server with Sufficient Permissions
* First, we could create an example user named `Cindy` with password `demo_passwd` of C's rabbitmq-server, and allow `Cindy` to listen to all the IPs:
  ```
  sudo rabbitmqctl add_user Cindy demo_passwd
  sudo rabbitmqctl set_permissions -p / Cindy ".*" ".*" ".*"
  ```
* When instantiating a Publisher/Subscriber on machine A or B, provide your credentials, for example:
  ```python
  import pika
  from pika_topic import Publisher, SingleSubscriber

  cred = pika.PlainCredentials("Cindy", "demo_passwd")
  conn = pika.BlockingConnection(
      pika.ConnectionParameters(
          host="192.168.3.7", port=5672, credentials=cred
      )
  )

  demo_publisher = Publisher("demo_remote_topic", conn)
  demo_subscriber = SingleSubscriber(
      "demo_remote_topic",
      queue_size=1,
      callback=lambda msg: print(msg),
      conn=conn
  )
  ```
* To use pika_topic.del and pika_topic.echo with new credentials, we can use:
  ```
  python -m pika_topic.del -n demo_remote_topic -ip 192.168.3.7 -a Cindy@demo_passwd
  ```
  ```
  python -m pika_topic.echo -n demo_remote_topic -ip 192.168.3.7 -a Cindy@demo_passwd
  ```

# Caution
* Codes not fully tested.
* It uses pickle to serialize/deserialize data, therefore, it is NOT SAFE.
* Currently only supports communication between pythons since it uses pickle. Maybe other data serialization/deserialization protocols would be added in the future.
