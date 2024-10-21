import pika
import argparse
from ._utils import *


def parse_opt():
    parser = argparse.ArgumentParser()
    default_param = pika.ConnectionParameters
    parser.add_argument("-n", "--name", type=str, default="", help="re pattern to filter name of queried exchanges")
    parser.add_argument("-u", "--user", type=str, default="", help="re pattern to filter user of queried exchanges")
    parser.add_argument("-v", "--vhost", type=str, default="", help="re pattern to filter vhost of queried exchanges")
    parser.add_argument("-y", "--yes", action="store_true", default=False, help="set true to skip the deletion confirm")
    parser.add_argument("-ip", "--ip", type=str, default="localhost", 
                        help="address of server hosting rabbitmq-server and rabbitmq_management")
    parser.add_argument("-mp", "--manage_port", type=int, default=15672, 
                        help="port of rabbitmq_management, default is 15672")
    parser.add_argument("-pp", "--pika_port", type=int, default=default_param.DEFAULT_PORT, 
                        help=f"address of rabbitmq-server, default is {default_param.DEFAULT_PORT}")
    default_auth = "@".join([default_param.DEFAULT_USERNAME, default_param.DEFAULT_PASSWORD])
    parser.add_argument("-a", "--auth", type=str, default=default_auth, 
                        help=f"auth to establish connection to host, format is username@passwd, default is {default_auth}")
    opt = parser.parse_args()
    return opt


def main():
    opt = parse_opt()
    filters = []
    if opt.name:
        filters.append(gen_name_filter(opt.name))
    if opt.user:
        filters.append(gen_user_filter(opt.user))
    if opt.vhost:
        filters.append(gen_vhost_filter(opt.vhost))
    
    ip = opt.ip
    rabbitmq_port = opt.manage_port
    username, password = opt.auth.strip().split("@")
    ret = fetch_all_exchanges(":".join([ip, str(rabbitmq_port)]), username, password)
    matches = find_matches(filters, ret)
    
    if len(matches) == 0:
        print("[INFO] No matches found.")
        return
    
    if not opt.yes:
        print("[INFO] Find matches:")
        for i, m in enumerate(matches):
            print("[{:>4d}]: {}".format(i+1, m))
        key = input("[INFO] Will delete totoal {} exchanges, continue? (Y/n): "
                    .format(len(matches)))
        key = key.strip().lower()
        if len(key) > 0 and (key != "y"):
            print("[INFO] Abortion.")
            return

    # delete matches
    pika_port = opt.pika_port
    cred = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=ip, port=pika_port, credentials=cred))
    channel = connection.channel()
    
    for m in matches:
        print("[INFO] Delete {}".format(m))
        channel.exchange_delete(m["name"])


if __name__ == "__main__":
    main()

