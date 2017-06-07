import urllib, urllib2, base64, os, hashlib, string, time, sys, json, zipfile, StringIO
import httplib as http
import jsxe

import requests, jwt

API_GET_CREDENTIALS = "http://api.jsx.exchange/v1/getContractCredentials"

def get_cred_dir(contract_id):
    home = os.path.expanduser("~/.jsxe/machines/")
    cred_dir = os.path.join(home, contract_id)
    jsxe.mkdir_p(cred_dir)
    return os.path.expanduser(cred_dir)

def get_credentials(contract_id):
    cred_dir = get_cred_dir(contract_id)
    
    try:
        js=json.load(file(os.path.join(cred_dir, "jsx.json")))
        print "# Loaded cached credentials for", contract_id
    except:
        print "# Please run `jsx fetch %s` first" % contract_id
        sys.exit()
        js = fetch_credentials(contract_id)
    print_env(js, cred_dir, contract_id)

def print_env(js, cred_dir, contract_id):
    if "IPv6-Addr" in js:
        ip = js["IPv6-Addr"]
    else:
        ip = js["IP-Addr"]
    env = """
export DOCKER_TLS_VERIFY="1"
export DOCKER_HOST="tcp://%(IP)s:%(PORT)s"
export DOCKER_CERT_PATH="%(CERTPATH)s"
export DOCKER_MACHINE_NAME="%(CID)s"
# Run this command to configure your shell: 
# eval $(jsx env %(CID)s)
""" % {"IP": ip, "PORT": js["Port"], "CERTPATH": cred_dir, "CID": contract_id}
    print env
    return env

def fetch_credentials(contract_id):
    cred_dir = get_cred_dir(contract_id)
    print "Will fetch credentials for contract id:", contract_id
    req = urllib2.Request(API_GET_CREDENTIALS+"?contractId=%s" % contract_id, None, jsxe.get_auth_headers())
    data = urllib2.urlopen(req).read()
    
    if len(data) < 10:
        print "No data available for contract ID", contract_id
        sys.exit(1)        
    try:
        js = json.loads(data)
    except ValueError:
        print "FATAL: could decode json", data
        sys.exit(2)
    
    file(os.path.join(cred_dir, "jsx.json"), "w+").write(data)
        
    zipf = StringIO.StringIO(base64.b64decode(js["Docker-Credentials-Zipfile"].replace(" ", "+")))
    
    jsxe.mkdir_p(cred_dir)
    
    zip_ref = zipfile.ZipFile(zipf, 'r')
    zip_ref.extractall(cred_dir)
    zip_ref.close()
    
    print_env(js, cred_dir, contract_id)
    return js
    
def main():
    if len(sys.argv) != 3 or (sys.argv[1] != "env" and sys.argv[1] != "fetch"):
        print "Usage: jsx env <contract_id>"
        sys.exit()
    
    if sys.argv[1] == "env": get_credentials(sys.argv[2])
    if sys.argv[1] == "fetch": fetch_credentials(sys.argv[2])
    # TODO: jsx ls ... buy/sell/close?

