from bs4 import BeautifulSoup
import requests
import time
import yagmail
import json
import threading
import math
from queue import Queue

print_lock = threading.Lock()


class Target:
    def __init__(self, recipient, target_url, target_label, interval):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label
        self.interval = interval


class Userconfig:
    def __init__(self):
        with open('config.json', 'r') as f:
            cfg = json.load(f)

            self.sender_username = cfg['sender_username']
            self.sender_pw = cfg['sender_pw']
            self.targets = []
            for target in cfg['targets']:
                self.targets.append(Target(**target))


def send(recipient, subject, body, sender, pw):
    try:
        yag = yagmail.SMTP(sender, pw)
        yag.send(to=recipient, subject=subject, contents=body)
        with print_lock:
            print('%s Email sent!' % subject)
    except Exception as e:
        with print_lock:
            print('email error: %s' % e)


def fullTextDiff(sender, pw, recipient, target_url, target_label, interval):
    before = None
    should_diff = False
    while True:
        r = requests.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        after = (soup.getText())

        if should_diff and before != after:
            subject = 'diff found in %s' % target_label
            body = target_url
            send(recipient, subject, body, sender, pw)

        else:
            before = after
            with print_lock:
                print('%s no diff' % target_label)

        should_diff = True
        time.sleep(math.ceil(float(interval) * 60))


def thread_queue():
    while True:
        current_target = target_queue.get()
        fullTextDiff(u_config.sender_username, u_config.sender_pw, current_target.recipient, current_target.target_url, current_target.target_label, current_target.interval) # noqa E501
        target_queue.task_done()


u_config = Userconfig()

target_queue = Queue()

for target in u_config.targets:
    t = threading.Thread(target=thread_queue)
    t.daemon = True
    t.start()
    target_queue.put(target)

target_queue.join()
