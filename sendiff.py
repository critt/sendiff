from bs4 import BeautifulSoup
import time
import yagmail
import json
import threading
import math
from queue import Queue
from selenium import webdriver

print_lock = threading.Lock()

str_none = 'none'

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
    def __init__(self, recipient, target_url, target_label, full_text, css_selector, xpath, interval_mins):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label
        self.full_text = full_text
        self.css_selector = css_selector
        self.xpath = xpath
        self.interval = interval_mins


class Email:
    def __init__(self, recipient, subject, body):
        self.recipient = recipient
        self.subject = subject
        self.body = body


class DiffFullText:
    def __init__(self):
        self.text_before = None

    def diff(self, driver):
        soup = BeautifulSoup(driver.page_source)
        text_now = (soup.getText())
        if self.text_before is not None and self.text_before != text_now:
            tmp_text_before = self.text_before
            self.text_before = text_now
            return Result(True, tmp_text_before, text_now, 'Full text diff found')
        self.text_before = text_now
        return Result(False, none, none, none)


class DiffCSSSelector:
    def __init__(self):
        self.text_before = None

    def diff(self, driver, css_selector):
        text_now = driver.find_element_by_css_selector(css_selector)
        if self.text_before is not None and self.text_before != text_now:
            tmp_text_before = self.text_before
            self.text_before = text_now
            return Result(True, tmp_text_before, text_now, 'CSS selector diff found')
        self.text_before = text_now
        return Result(False, none, none, none)

        
class DiffXPath:
    def __init__(self):
        self.text_before = None

    def diff(self, driver, xpath):
        text_now = driver.find_element_by_xpath(xpath)
        if self.text_before is not None and self.text_before != text_now:
            tmp_text_before = self.text_before
            self.text_before = text_now
            return Result(True, tmp_text_before, text_now, 'XPath diff found')
        self.text_before = text_now
        return Result(False, none, none, none)


class Result:
    def __init__(self, is_diff, obj_before, obj_after, message):
        this.is_diff = is_diff
        this.obj_before = obj_before
        this.obj_after = obj_after
        this.message - message


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
    diff_css_selector = DiffCSSSelector()
    diff_xpath = DiffXPath()

    results = []

    while True:
        diff_found = False

        driver = webdriver.Chrome()
        driver.implicitly_wait(30)
        driver.get(target.target_url)

        if(target.full_text):
            result = diff_full_text.diff(driver)
            if(result.is_diff):
                results.add(result)
            diff_found = True

        if(target.css_selector is not str_none):
            rssult = diff_css_selector.diff(driver, target.css_selector)
            if(result.is_diff):
                results.add(result)
            diff_found = True

        if(target.xpath is not str_none):
            result = diff_xpath.diff(driver, target.xpath)
            if(result.is_diff):
                results.add(result)
            diff_found = True

        if diff_found:
            with print_lock:
                print('%s diff found' % target.target_label)

            subject = 'diff found in %s' % target.target_label
            body
            for result in results:
                body = body + result.message + '\n'
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
