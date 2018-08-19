from bs4 import BeautifulSoup
import requests
import time
import yagmail
import json
import threading
import math
from queue import Queue

print_lock = threading.Lock()


class Userconfig:
    def __init__(self):
        with open('config.json', 'r') as f:
            cfg = json.load(f)

            self.sender_username = cfg['sender_username']
            self.sender_pw = cfg['sender_pw']
            self.targets = []
            for target in cfg['targets']:
                self.targets.append(Target(**target))


class Target:
    def __init__(self, recipient, target_url, target_label, interval):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label
        self.interval = interval


class Email:
    def __init__(self, recipient, subject, body):
        self.recipient = recipient
        self.subject = subject
        self.body = body


def send(email):
    with print_lock:
        print('%s sending' % email.subject)
    try:
        yag = yagmail.SMTP(u_config.sender_username, u_config.sender_pw)
        yag.send(to=email.recipient, subject=email.subject, contents=email.body) # noqa E501
        with print_lock:
            print('%s Email sent!' % email.subject)
    except Exception as e:
        with print_lock:
            print('email error: %s' % e)


def fullTextDiff(recipient, target_url, target_label, interval):
    before = None
    should_diff = False
    for n in range(0, 3):
        r = requests.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        after = (soup.getText())

        if should_diff and before != after:

            with print_lock:
                print('%s diff found' % target_label)

            subject = 'diff found in %s' % target_label
            body = target_url
            # send(Email(recipient, subject, body))
            send_queue.put(Email(recipient, subject, body))

        else:
            before = after
            with print_lock:
                print('%s no diff' % target_label)

        should_diff = True
        time.sleep(math.ceil(float(interval) * 60))


def request_queue():
    while True:
        current_target = scan_queue.get()
        fullTextDiff(current_target.recipient, current_target.target_url, current_target.target_label, current_target.interval) # noqa E501
        scan_queue.task_done()


def email_queue():
    while True:
        current_email = send_queue.get()
        send(current_email)
        send_queue.task_done()


u_config = Userconfig()

scan_queue = Queue()
send_queue = Queue()

for target in u_config.targets:
    t = threading.Thread(target=request_queue)
    t.daemon = True
    t.start()
    scan_queue.put(target)


t = threading.Thread(target=email_queue)
t.daemon = True
t.start()

scan_queue.join()
send_queue.join()
