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


def main():
    opt = parse_opt()
    filters = []
    if opt.name:
        filters.append(gen_name_filter(opt.name))
    if opt.user:
        filters.append(gen_user_filter(opt.user))
    if opt.vhost:
        filters.append(gen_vhost_filter(opt.vhost))
    
    username, password = opt.auth.strip().split(":")
    ret = fetch_all_exchanges(opt.manage_server.strip(), username, password)
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
    pika_ip, pika_port = opt.pika_server.strip().split(":")
    cred = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=pika_ip, port=int(pika_port), credentials=cred))
    channel = connection.channel()
    
    for m in matches:
        print("[INFO] Delete {}".format(m))
        channel.exchange_delete(m["name"])


if __name__ == "__main__":
    main()

