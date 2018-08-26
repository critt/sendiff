from bs4 import BeautifulSoup
import time
import yagmail
import json
import threading
import math
from queue import Queue
from selenium import webdriver

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
    def __init__(self, recipient, target_url, target_label, interval_mins):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label
        self.interval = interval_mins


class Email:
    def __init__(self, recipient, subject, body):
        self.recipient = recipient
        self.subject = subject
        self.body = body


class DiffFullText:
    def __init__(self):
        self.text_before = None

    def diff(self, request_now):
        soup = BeautifulSoup(request_now, 'lxml')
        text_now = (soup.getText())
        if self.text_before is not None and self.text_before != text_now:
            self.text_before = text_now
            return True
        self.text_before = text_now
        return False


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


def request_loop(target):
    diff_full_text = DiffFullText()
    while True:
        driver = webdriver.Chrome()
        driver.implicitly_wait(30)
        driver.get(target.target_url)
        is_diff = diff_full_text.diff(driver.page_source)

        if is_diff:
            with print_lock:
                print('%s diff found' % target.target_label)

            subject = 'diff found in %s' % target.target_label
            body = target.target_url
            email_queue.put(Email(target.recipient, subject, body))

        else:
            with print_lock:
                print('%s no diff' % target.target_label)

        time.sleep(math.ceil(float(target.interval) * 60))


def process_request():
    while True:
        request_loop(request_queue.get())
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
    target_thread = threading.Thread(target=process_request)
    target_thread.daemon = True
    target_thread.start()
    request_queue.put(target)

email_thread = threading.Thread(target=process_email)
email_thread.daemon = True
email_thread.start()

request_queue.join()
email_queue.join()
