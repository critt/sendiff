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


def send_email(email):
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


def full_text_diff(recipient, target_url, target_label, interval):
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
            email_queue.put(Email(recipient, subject, body))

        else:
            before = after
            with print_lock:
                print('%s no diff' % target_label)

        should_diff = True
        time.sleep(math.ceil(float(interval) * 60))


def process_request():
    while True:
        current_target = request_queue.get()
        full_text_diff(current_target.recipient, current_target.target_url, current_target.target_label, current_target.interval) # noqa E501
        request_queue.task_done()


def process_email():
    while True:
        current_email = email_queue.get()
        send_email(current_email)
        email_queue.task_done()


u_config = Userconfig()
request_queue = Queue()
email_queue = Queue()

for target in u_config.targets:
    t = threading.Thread(target=process_request)
    t.daemon = True
    t.start()
    request_queue.put(target)

t = threading.Thread(target=process_email)
t.daemon = True
t.start()

request_queue.join()
email_queue.join()
