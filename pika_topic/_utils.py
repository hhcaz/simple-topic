import re
import json
import requests


def fetch_all_exchanges(host_port: str, username: str, passwd: str):
    url = f"http://{host_port}/api/exchanges"
    response = requests.get(url, auth=(username, passwd))
    if response.text:
        ret = json.loads(response.text)
        if not isinstance(ret, list):
            print(ret)
            print("Error when fetching exchanges.")
    else:
        ret = []
    return ret


def find_matches(filters: list, candidates: list):
    matches = []
    for exchange in candidates:
        if exchange["user_who_performed_action"] == "rmq-internal":
            # skip internal exchanges owned by rabbitmq
            continue
        
        for f in filters:
            if not f(exchange):
                break
        else:
            # all conditions satisefy, delete
            matches.append(exchange)
    return matches


def parse_flag(flag: str = None):
    if isinstance(flag, int):
        return flag
    elif flag is None:
        return 0
    else:
        assert isinstance(flag, str)
        flag = flag.strip()
        if len(flag) > 0:
            flag = eval(flag)
        else:
            flag = 0
        return flag


def gen_name_filter(pattern: str, flag: str = None):
    re_pattern: re.Pattern = re.compile(pattern, parse_flag(flag))
    
    def filter_func(exchange: dict):
        return re_pattern.search(exchange["name"]) is not None
    return filter_func


def gen_user_filter(pattern: str, flag: str = None):
    re_pattern: re.Pattern = re.compile(pattern, parse_flag(flag))
    
    def filter_func(exchange: dict):
        return re_pattern.search(exchange["user_who_performed_action"]) is not None
    return filter_func


def gen_vhost_filter(pattern: str, flag: str = None):
    re_pattern: re.Pattern = re.compile(pattern, parse_flag(flag))
    
    def filter_func(exchange: dict):
        return re_pattern.search(exchange["vhost"]) is not None
    return filter_func
