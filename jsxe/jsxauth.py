import urllib, urllib2, base64, os, hashlib, string, time, sys, json
import httplib as http

import requests, jwt

# https://stackoverflow.com/a/600612
import errno    
import os

def mkdir_p(path):
    path = os.path.expanduser(path)
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

TOKENSTORE_DIR = "~/.jsxe/"
TOKENSTORE = os.path.expanduser(os.path.join(TOKENSTORE_DIR,"token.json"))

interactive_allowed = True

my_auth0_dom = "jsx.eu.auth0.com"
client_id = "NXGCuP721i8EqIJT2sNIZuP50vIRDjmO"
audience = "https://interpreter.jsx.exchange"
redir_uri = "https://www.wolframcloud.com/objects/e21089ba-ec0d-4495-ad40-b92f207c488e"
scopes = "openid%20profile%20email%20offline_access"

def get_code(state):
    link = "https://www.wolframcloud.com/objects/794a32a4-ba90-42cc-b971-cc1512d72e96?state=%s" % state
    f = urllib.urlopen(link)
    return f.read()

def base64URLEncode(s):
    return base64.b64encode(s).replace("+", '-').replace("/", '_').replace("=", '');
    # return base64.b64encode(s)


def sha256(buf):
    m = hashlib.sha256()
    m.update(buf)
    return m.digest()

def interactive_get_token():
    verifier = base64URLEncode(os.urandom(32))
    challenge = base64URLEncode(sha256(verifier))
    sessid = base64URLEncode(os.urandom(5))
    code_orig = get_code(sessid)
    weblink = string.Template("https://${YOUR_AUTH0_DOMAIN}/authorize?scope=${SCOPES}&audience=${AUD}&response_type=code&client_id=${YOUR_CLIENT_ID}&code_challenge=${challenge}&code_challenge_method=S256&redirect_uri=${REDIR}&state=${STATEID}")
    print "-"*10
    print "Now navigate your browser to:", weblink.substitute({"YOUR_AUTH0_DOMAIN" : my_auth0_dom, "YOUR_CLIENT_ID": client_id, "challenge":challenge, "AUD": audience, "REDIR": redir_uri, "SCOPES": scopes, "STATEID": sessid})
    print "-"*10
    # print "Your verifier will be:", verifier
    # print "Your challenge will be:", challenge

    print "Waiting for you to auth... "
    time.sleep(10)

    i = 0
    while True:
        code_new = get_code(sessid)
        print ".",
        sys.stdout.flush()
        i += 1
        if code_new != code_orig or i > 10:
            break
        time.sleep(10)

        if i > 10:
            print "Time out getting code callback"
            return None

    print "New code is:", code_new

    print "Getting the token..."

    payload = '{"grant_type":"authorization_code","client_id": "%(YOUR_CLIENT_ID)s","code_verifier": "%(YOUR_GENERATED_CODE_VERIFIER)s","code": "%(YOUR_AUTHORIZATION_CODE)s","redirect_uri": "%(REDIR)s", "scope":"openid profile email"}' % {"YOUR_AUTH0_DOMAIN" : my_auth0_dom, "YOUR_CLIENT_ID": client_id, "challenge":challenge, "YOUR_GENERATED_CODE_VERIFIER": verifier, "YOUR_AUTHORIZATION_CODE": code_new, "REDIR": redir_uri}

    # print "Payload:", payload

    headers = { 'content-type': "application/json" }
    
    conn = http.HTTPSConnection(my_auth0_dom)
    conn.request("POST", "/oauth/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    
    # print "The token payload is:", data

    # return json.loads(data.decode("utf-8").split("\n")[1])
    return json.loads(data.decode("utf-8"))

def refresh_token(refresh_token):
    payload = "{ \"grant_type\": \"refresh_token\", \"client_id\": \"%(client_id)s\", \"refresh_token\": \"%(refresh_token)s\", \"scope\":\"openid profile email\" }" % {"client_id": client_id , "refresh_token": refresh_token }
    
    headers = { 'content-type': "application/json" }
    
    conn = http.HTTPSConnection(my_auth0_dom)
    conn.request("POST", "/oauth/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    
    # print "The token payload is:", data
    
    return json.loads(data.decode("utf-8"))

token = {}
auth_headers = {}

def create_auth_headers(access_token):
    return { 'authorization': "Bearer %s" % access_token }

def read_token():
    global token
    global auth_headers
    mkdir_p(TOKENSTORE_DIR)
    try:
        token = json.load(file(TOKENSTORE))
    except IOError:
        if interactive_allowed:
            token = interactive_get_token()
        else:
            print "FATAL: interactivity not allowed"
            return None
    try:
        json.dump(token, file(TOKENSTORE, "w+"))
    except IOError:
        print "ERR: Could not save token!"
    return True


def test_jwt_exp(tkn):
    exp = jwt.decode(tkn, verify=False)["exp"]
    return exp - time.time() > 0

def get_auth_headers():
    global token, auth_headers
    if len(token) == 0:
        if not read_token():
            print "FATAL: could not read token"
            return None
        
    if len(auth_headers) == 0:
        auth_headers = create_auth_headers(token["id_token"])
    if not test_jwt_exp(auth_headers['authorization'].split()[1]):
        if not "refresh_token" in token:
            print "FATAL: no refresh token and token outdated. Can not authenticate with tokens."
            return {}
        else:
            token = refresh_token(token["refresh_token"])
            auth_headers = create_auth_headers(token["id_token"])
    return auth_headers
    

if __name__ == '__main__':
    print interactive_get_token()
    
