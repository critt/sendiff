# sendiff

##### Sends Gmail emails when websites change

#### Quick Start

1. Copy ```config_bak.json``` to ```config.json```. Add your sender account info and your list of targets to ```config.json```
  *  ```$ cp config_bak.json config.json && nano config.json```
2. Run the script
  *  ```$ python3 sendiff.py```

For problems with SMTP auth errors: https://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python