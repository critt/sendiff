from bs4 import BeautifulSoup
import time
import yagmail
import json
import threading
import math
import sys
import getopt
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
    def __init__(self, recipient, target_url, target_label, cookies, full_text, css_selector, xpath, interval_mins, enabled):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label
        self.cookies = []
        for cookie in cookies:
            self.cookies.append(Cookie(**cookie))
        self.full_text = full_text
        self.css_selector = css_selector
        self.xpath = xpath
        self.interval = interval_mins
        self.enabled = enabled


class Cookie:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Email:
    def __init__(self, recipient, subject, body):
        self.recipient = recipient
        self.subject = subject
        self.body = body


class Result:
    def __init__(self, is_diff, obj_before, obj_after, message):
        self.is_diff = is_diff
        self.obj_before = obj_before
        self.obj_after = obj_after
        self.message = message


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
        return Result(False, None, None, None)


class DiffCSSSelector:
    def __init__(self):
        self.text_before = None

    def diff(self, driver, css_selector):
        try:
            obj_now = driver.find_element_by_css_selector(css_selector)
        except Exception:
            with print_lock:
                print('css_selector: unable to find element')
            return Result(False, None, None, None)

        text_now = obj_now.text
        print('DiffCSSSelector, text_now=%s' % text_now)
        if self.text_before is not None and self.text_before != text_now:
            tmp_text_before = self.text_before
            self.text_before = text_now
            return Result(True, tmp_text_before, text_now, 'CSS selector diff found')
        self.text_before = text_now
        return Result(False, None, None, None)


class DiffXPath:
    def __init__(self):
        self.text_before = None

    def diff(self, driver, xpath):
        try:
            obj_now = driver.find_element_by_xpath(xpath)
        except Exception:
            with print_lock:
                print('xpath: unable to find element')
            return Result(False, None, None, None)

        text_now = obj_now.text
        print('DiffXPath, text_now=%s' % text_now)
        if self.text_before is not None and self.text_before != text_now:
            tmp_text_before = self.text_before
            self.text_before = text_now
            return Result(True, tmp_text_before, text_now, 'XPath diff found')
        self.text_before = text_now
        return Result(False, None, None, None)


u_config = Userconfig()
request_queue = Queue()
email_queue = Queue()

str_none = 'none'
str_usage = 'usage: sindiff.py <option>'
str_help = '%s\noptions:\n\t-h : help\n\t-t <index of target to test> : test a target without a headless browser' % str_usage
str_idx_err = 'index %s out of bounds.\nnum targets=%s\nlast index=%s'

print_lock = threading.Lock()


def send_email(email):
    with print_lock:
        print('%s sending' % email.subject)
    try:
        yag = yagmail.SMTP(u_config.sender_username, u_config.sender_pw)
        yag.send(to=email.recipient, subject=email.subject, contents=email.body)
        with print_lock:
            print('%s Email sent!' % email.subject)
    except Exception as e:
        with print_lock:
            print('email error: %s' % e)


def request_loop(target, is_test):
    if is_test:
        driver = webdriver.Chrome()
    else:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(chrome_options=options)
    driver.implicitly_wait(30)
    diff_full_text = DiffFullText()
    diff_css_selector = DiffCSSSelector()
    diff_xpath = DiffXPath()
    results = []
    keep_going = True

    if(len(target.cookies) > 0):
        driver.get(target.target_url)
        time.sleep(10)
        for cookie in target.cookies:
            driver.add_cookie(json.loads(json.dumps({'name': (cookie.key), 'value': (cookie.value)})))

    while keep_going:
        diff_found = False

        driver.get(target.target_url)
        if(target.full_text):
            result = diff_full_text.diff(driver)
            if(result.is_diff and not is_test):
                results.append(result)
                diff_found = True

        if(target.css_selector is not str_none):
            result = diff_css_selector.diff(driver, target.css_selector)
            if(result.is_diff and not is_test):
                results.append(result)
                diff_found = True

        if(target.xpath is not str_none):
            result = diff_xpath.diff(driver, target.xpath)
            if(result.is_diff and not is_test):
                results.append(result)
                diff_found = True

        if is_test:
            keep_going = False
        else:
            if diff_found:
                with print_lock:
                    print('%s diff found' % target.target_label)

                subject = 'diff found in %s' % target.target_label
                body = ''
                for result in results:
                    body = body + result.message + '\n' + 'before:\n\t%s\n' % result.obj_before + 'after:\n\t%s\n' % result.obj_after + '\n'

                with print_lock:
                    print('body=\n%s' % body)
                email_queue.put(Email(target.recipient, subject, body))
            else:
                with print_lock:
                    print('%s no diff' % target.target_label)

        if keep_going:
            time.sleep(math.ceil(float(target.interval) * 60))


def process_request():
    while True:
        request_loop(request_queue.get(), False)
        request_queue.task_done()


def process_email():
    while True:
        current_email = email_queue.get()
        send_email(current_email)
        email_queue.task_done()


def parse_args(argv):
    try:
        opts, args = getopt.getopt(argv, "ht:")
    except getopt.GetoptError:
        print(str_usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(str_help)
            sys.exit()
        if opt == '-t':
            print('index: %s' % arg)
            if(int(arg) >= len(u_config.targets)):
                print(str_idx_err % (arg, len(u_config.targets), len(u_config.targets) - 1))
                sys.exit()
            else:
                test(int(arg))
                return
    main()


def test(idx):
    target = u_config.targets[idx]
    request_loop(target, True)
    sys.exit()


def main():
    req_thread_count = 0
    for target in u_config.targets:
        if target.enabled:
            req_thread_count += 1
            print('Adding to queue: %s' % target.target_label)
            target_thread = threading.Thread(target=process_request)
            target_thread.daemon = True
            target_thread.start()
            request_queue.put(target)

    print('Request thread count: %s' % req_thread_count)

    if req_thread_count > 0:
        email_thread = threading.Thread(target=process_email)
        email_thread.daemon = True
        email_thread.start()

        request_queue.join()
        email_queue.join()


if __name__ == "__main__":
    parse_args(sys.argv[1:])
