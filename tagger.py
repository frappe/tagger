import hmac, json
from hashlib import sha1
from os.path import abspath, normpath, dirname, join
from urllib.parse import urlparse

from flask import Flask, request, abort
from github import Github

app = Flask(__name__)
with open ('config.json') as f:
	config = json.load(f)

@app.route('/', methods=['POST'])
def tagger():
	authenticate_request()

	payload = request.get_json()

	# docs-required status check
	if not payload.get('context'):
		repo = get_repo(payload)
		head_sha = payload.get('pull_request', {}).get('head', {}).get('sha', None)
		title = payload.get('pull_request', {}).get('title', '')
		body = payload.get('pull_request', {}).get('body', '')
		if title.startswith('feat') and head_sha:
			status = 'pending'
			description = 'Documentation required'
			if docs_link_exists(body):
				status = 'success'
				description = 'Documentation link added'
			repo.get_commit(head_sha).create_status(
				status,
				target_url="https://github.com/frappe/erpnext/wiki/Updating-Documentation",
				description=description,
				context="docs-required"
			)

	# Semantic PRs - Label if pending
	if payload.get('context') == 'Semantic Pull Request':
		if payload.get('state') == 'pending':
			add_label_to_pr(payload, 'needs-semantic-title')
		else:
			remove_label_from_pr(payload, 'needs-semantic-title')

	# Codacy - Label if failed, remove if success
	elif payload.get('context') == 'Codacy/PR Quality Review':
		if payload.get('state') == 'failure':
			add_label_to_pr(payload, 'review-codacy')
		elif payload.get('state') == 'success':
			remove_label_from_pr(payload, 'review-codacy')

	# Travis CI - Label if errored or failed, remove if success
	elif payload.get('context') == 'continuous-integration/travis-ci/pr':
		if payload.get('state') in ['error', 'failure']:
			add_label_to_pr(payload, 'travis-failing')
		elif payload.get('state') == 'success':
			remove_label_from_pr(payload, 'travis-failing')

	# CicleCI - Label if errored or failed, remove if success
	elif payload.get('context') == 'ci/circleci':
		if payload.get('state') in ['error', 'failure']:
			add_label_to_pr(payload, 'circleci-failing')
		elif payload.get('state') == 'success':
			remove_label_from_pr(payload, 'circleci-failing')

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

def get_repo(payload):
	g = Github(config.get('gh_user'), config.get('gh_pass'))
	return g.get_repo(payload.get('repository').get('full_name'))

def get_pr_to_modify(payload):
	pr_no = payload.get('number')
	if not pr_no:
		commit_sha = payload.get('commit', {}).get('sha')
		if not commit_sha: return
		res = g.search_issues('sha:' + commit_sha)
		if not res: return
		pr_no = res[0].number
	return get_repo(payload).get_pull(pr_no)

def uri_validator(x):
	result = urlparse(x)
	return all([result.scheme, result.netloc, result.path])

def docs_link_exists(body):
	docs_repos = ["erpnext_documentation", "erpnext_com", "frappe_io"]

	for line in body.splitlines():
		for word in line:
			if word.startswith('http') and uri_validator(word):
				parsed_url = urlparse(word)
				if parsed_url.netloc == "github.com":
					_, org, repo, _type, ref = parsed_url.path.split('/')
					if org == "frappe" and repo in docs_repos:
						return True
