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
    parser.add_argument("-ms", "--manage_server", type=str, default="localhost:15672", 
                        help="address of rabbitmq_management server, default is \"localhost:15672\"")
    default_pika = ":".join([default_param.DEFAULT_HOST, str(default_param.DEFAULT_PORT)])
    parser.add_argument("-ps", "--pika_server", type=str, default=default_pika, 
                        help="address of pika server, default is \"{}\"".format(default_pika))
    default_auth = ":".join([default_param.DEFAULT_USERNAME, default_param.DEFAULT_PASSWORD])
    parser.add_argument("-a", "--auth", type=str, default=default_auth, 
                        help="auth to establish connection to host, format is username:passwd, default is \"{}\"".format(default_auth))
    opt = parser.parse_args()
    return opt


class DataCallback(object):
    def __init__(self, update_alpha=0.1):
        self.update_alpha = update_alpha
        self.prev_t = None
        self.counts = 0
        self.fps = 0
    
    def update(self, data):
        curr_t = time.perf_counter()
        if self.prev_t is None:
            fps_new = 0.0
        else:
            fps_new = 1.0 / (curr_t - self.prev_t)
        self.prev_t = curr_t
        self.fps = fps_new * self.update_alpha + self.fps * (1 - self.update_alpha)
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
    
    username, password = opt.auth.strip().split(":")
    ret = fetch_all_exchanges(opt.manage_server.strip(), username, password)
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
    
    data_callback = DataCallback(update_alpha=0.1)
    
    pika_ip, pika_port = opt.pika_server.strip().split(":")
    cred = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=pika_ip, port=int(pika_port), credentials=cred))
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

