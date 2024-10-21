import pika
import time
import argparse
import numpy as np
from ._utils import *
from pprint import pprint
from .sub import Subscriber


def parse_opt():
    parser = argparse.ArgumentParser()
    default_param = pika.ConnectionParameters
    parser.add_argument("-n", "--name", type=str, default="", help="re pattern to filter name of queried exchanges")
    parser.add_argument("-u", "--user", type=str, default="", help="re pattern to filter user of queried exchanges")
    parser.add_argument("-v", "--vhost", type=str, default="", help="re pattern to filter vhost of queried exchanges")
    parser.add_argument("-p", "--precision", type=int, default=3, help="displayed precision of numpy arrays in message, "
                        "default is 3")
    parser.add_argument("-ip", "--ip", type=str, default=default_param.DEFAULT_HOST, 
                        help="address of server hosting rabbitmq-server and rabbitmq_management, "
                            f"default is {default_param.DEFAULT_HOST}")
    parser.add_argument("-mp", "--manage_port", type=int, default=15672, 
                        help="port of rabbitmq_management, default is 15672")
    parser.add_argument("-pp", "--pika_port", type=int, default=default_param.DEFAULT_PORT, 
                        help=f"address of rabbitmq-server, default is {default_param.DEFAULT_PORT}")
    default_auth = "@".join([default_param.DEFAULT_USERNAME, default_param.DEFAULT_PASSWORD])
    parser.add_argument("-a", "--auth", type=str, default=default_auth, 
                        help=f"auth to establish connection to host, format is username@passwd, default is {default_auth}")
    opt = parser.parse_args()
    return opt


class DataCallback(object):
    def __init__(self, win_size=100):
        self.dts = []
        self.win_size = win_size
        self.prev_t = None
        self.counts = 0
    
    def update(self, data):
        curr_t = time.perf_counter()
        if self.prev_t is None:
            self.prev_t = curr_t
            return
        else:
            dt_new = curr_t - self.prev_t
            self.prev_t = curr_t
            self.dts.append(dt_new)
            if len(self.dts) > self.win_size:
                self.dts.pop(0)
        
        self.fps = 1.0 / np.mean(self.dts)
        self.counts += 1
        
        print("-"*61)
        print("[INFO] Counts: {}".format(self.counts))
        print("[INFO] FPS: {}".format(self.fps))
        print("[INFO] Data: ")
        pprint(data, sort_dicts=False)


def main():
    opt = parse_opt()
    filters = []
    if opt.name:
        filters.append(gen_name_filter(opt.name))
    if opt.user:
        filters.append(gen_user_filter(opt.user))
    if opt.vhost:
        filters.append(gen_vhost_filter(opt.vhost))
    
    precision = opt.precision
    if precision > 0:
        np.set_printoptions(precision, suppress=True)

    ip = opt.ip
    rabbitmq_port = opt.manage_port
    username, password = opt.auth.strip().split("@")
    ret = fetch_all_exchanges(":".join([ip, str(rabbitmq_port)]), username, password)
    matches = find_matches(filters, ret)
    
    if len(matches) > 1:
        print("*"*61)
        print("[INFO] Find multiple matches:")
        for i, m in enumerate(matches):
            print("[{:>4d}]: {}".format(i, m))
        print("*"*61)
        inp = ""
        while len(inp) == 0:
            inp = input("[INFO] Input index to select: ").strip()
        index = int(inp)
        match = matches[index]
    elif len(matches) == 0:
        print("[INFO] No match found.")
        return
    else:
        match = matches[0]
    
    data_callback = DataCallback()
    
    pika_port = opt.pika_port
    cred = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=ip, port=pika_port, credentials=cred))
    subscriber = Subscriber(connection)
    subscriber.subscribe(
        topic=match["name"],
        queue_size=2,
        callback=data_callback.update
    )
    try:
        print("[INFO] Waiting for messages...")
        subscriber.spin()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

