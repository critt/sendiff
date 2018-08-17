from bs4 import BeautifulSoup
import requests
import time
import yagmail
import json


class Target:
    def __init__(self, recipient, target_url, target_label):
        self.recipient = recipient
        self.target_url = target_url
        self.target_label = target_label


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
        print('Email sent!')
    except Exception as e:
        print('email error: %s' % e)
        e.print_exc()


def fullTextDiffThread(sender, pw, recipient, target_url, target_label):
    print(recipient)
    before = None
    n = 0
    while 1 > 0:
        print(n)
        r = requests.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        after = (soup.getText())

        if n != 0 and before != after:

            subject = 'diff found in %s' % target_label
            body = target_url

            send(recipient, subject, body, sender, pw)

        else:
            before = after
            print('no diff')

        # sleep in seconds
        n = 1
        time.sleep(20)


def main(u_config):
    for target in u_config.targets:
        m_recipient = target.recipient
        m_target_url = target.target_url
        m_target_label = target.target_label
        fullTextDiffThread(u_config.sender_username, u_config.sender_pw, m_recipient, m_target_url, m_target_label) # noqa E501


u_config = Userconfig()
main(u_config)
