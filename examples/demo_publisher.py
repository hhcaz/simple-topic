import numpy as np
from pika_topic import Publisher, Rate


publisher0 = Publisher("demo_topic_0")
publisher1 = Publisher("demo_topic_1")
rate = Rate(50)  # Hz

print("[INFO] Start publishing...")
frame_id = 0
while True:
    publisher0.publish([f"frame {frame_id} of publisher 0:", np.random.rand(3)])
    publisher1.publish([f"frame {frame_id} of publisher 1:", np.random.rand(3)])
    frame_id += 1
    rate.sleep()
