# tagger
A simple Flask app to automatically label GitHub PRs.


---


### Creating a webhook:
1. Set Payload URL to your intended server (e.g. `http://123.231.123.231:8000`).
2. Set Content Type to `application/json`.
3. Set the secret key to whatever you like (we'll use this later).
4. Configure the webhook to trigger on Status events.
5. We can save the webhook now.


---


### Setting up a local environment:

1. Clone this repository in your desired location:
```
git clone https://github.com/erpnext/tagger
```

2. Change working directory:
```
cd tagger
```


3. Create a virtual enviroment using Python 3:
```
python3 - m venv .venv
```

4. Activate virtual environment:
```
source .venv/bin/activate
```

5. Install requirements:
```
pip install -r requirements.txt
```

6. Create a config.json file with following keys:
- `request_secret`: The secret code you used while setting up a webhook.
- `gh_user`: Github username using which PRs will be tagged automatically.
- `gh_pass`: Password for the username specified above.

7. Run flask to listen for webhook calls:
```
export FLASK_APP=tagger
flask run -h 0.0.0.0 -p 8000 --reload --debugger
```

--- 
### Setting up a server to listen to webhook events:

1. Follow steps (1 - 6) in the section titled `Setting up a local environment`.
2. If you choose to use Ubuntu 18.04 LTS, uWSGI and Nginx for your purposes, [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04) is recommended.
