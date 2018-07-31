from time import gmtime, strftime, sleep
from bs4 import BeautifulSoup
import requests
import time
import json
import smtplib

target_url = 'https://www.timeanddate.com/worldclock/?'
target_label = 'HDTGM'
name_data = '  '

n = 0
while 1 > 0:
        print(n)
        r = requests.get(target_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        tmp = (soup.getText())
        #print tmp
        if name_data != tmp and n != 0:
            #send email
            gmail_user = 'user@gmail.com'  
            gmail_password = 'password'

            sent_from = gmail_user  
            to = ['christopher.barrett.sims@gmail.com']  
            subject = 'diff found in %s' % target_label
            body = target_url
            message = 'Subject: {}\n\n{}'.format(subject, body)

            try:  
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(gmail_user, gmail_password)
                server.sendmail(sent_from, to, message)
                server.close()

                print('Email sent!')
            except Exception as e:  
                print('email error: %s' % e)
                traceback.print_exc()

        else:
            name_data = tmp
            print('no diff')
        #sleep in seconds
        n = 1
        time.sleep(20)