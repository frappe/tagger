import hmac, json
from hashlib import sha1
from os.path import abspath, normpath, dirname, join

from flask import Flask, request, abort
from github import Github

app = Flask(__name__)
with open ('config.json') as f:
	config = json.load(f)

@app.route('/', methods=['POST'])
def tagger():
	authenticate_request()

	payload = request.get_json()
	if payload.get('context') == 'ci/circleci':
		if payload.get("state") == "error":
			add_label_to_pr(payload, "circleci-failed")
		else:
			remove_label_from_pr(payload, "circleci-failed")

	return json.dumps({'status': 'done'})

def authenticate_request():
	path = normpath(abspath(dirname(__file__)))
	with open(join(path, 'config.json'), 'r') as f:
		config = json.load(f)

	secret = config.get('request_secret')
	header_signature = request.headers.get('X-Hub-Signature')
	if header_signature is None:
		abort(403)

	sha_name, signature = header_signature.split('=')
	if sha_name != 'sha1':
		abort(501)

	mac = hmac.new(secret.encode(), msg=request.data, digestmod='sha1')
	if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
		abort(403)

def add_label_to_pr(payload, label_name):
	pr = get_pr_to_modify(payload)
	for label in pr.labels:
		if label.name == label_name:
			return
	pr.add_to_labels(label_name)

def remove_label_from_pr(payload, label_name):
	pr = get_pr_to_modify(payload)
	for label in pr.labels:
		if label.name == label_name:
			pr.remove_from_labels(label_name)
			return

def get_pr_to_modify(payload):
	g = Github(config.get('gh_user'), config.get('gh_pass'))
	commit_sha = payload.get('commit', {}).get('sha')
	if not commit_sha: return
	res = g.search_issues('sha:' + commit_sha)
	if not res: return
	pr_no = res[0].number
	return g.get_repo(payload.get('repository').get('full_name')).get_pull(pr_no)
