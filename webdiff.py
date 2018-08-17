from time import gmtime, strftime, sleep
from bs4 import BeautifulSoup
import requests
import time
import json
import json
import yagmail

email = None
pw = None
recipient = None
target_url = None
target_label = None

with open('config.json') as json_file:  
    data = json.load(json_file)

    email = data['email']
    pw = data['pw']
    recipient = data['recipient']
    target_url = data['target_url']
    target_label = data['target_label']


compare_to = None

n = 0
while 1 > 0:
        print(n)
        r = requests.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        tmp = (soup.getText())
        #print tmp
        if compare_to != tmp and n != 0:
            #send email
            gmail_user = email 
            gmail_password = pw

            sent_from = gmail_user  
            to = [recipient]  
            subject = 'diff found in %s' % target_label
            body = target_url

            try:  
                yag = yagmail.SMTP(email, pw)
                yag.send(to = recipient, subject = subject, contents = body)
                print('Email sent!')
            except Exception as e:  
                print('email error: %s' % e)
                traceback.print_exc()

        else:
            compare_to = tmp
            print('no diff')
        #sleep in seconds
        n = 1
        time.sleep(20)