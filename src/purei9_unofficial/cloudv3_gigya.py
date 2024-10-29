import requests
import time
import random
import sys
import hashlib
import hmac
import base64
import binascii
import urllib.parse

from .util import do_http, CachedData

def gigya_sign(sessionSecret, httpMethod, baseUrl, params):
    params = urllib.parse.quote(urllib.parse.urlencode(params))
    #print("urlparams\t" + params)
    key = base64.b64decode(sessionSecret.encode("ascii"))
    d = urllib.parse.quote(httpMethod) + "&" + urllib.parse.quote(baseUrl, safe="") + "&" + params
    #print("baseSignature\t" + d)
    return base64.urlsafe_b64encode(hmac.new(key, d.encode("utf-8"), hashlib.sha1).digest()).decode("ascii")

def gigya_test_sign():
    """
    Test data from https://github.com/SAP/gigya-android-sdk/blob/main/sdk-core/src/test/java/com/gigya/android/utils/AuthUtilsTest.java
    Note that this coe has a bug: The session secret is not a properly padded base64 string, so we need to fix this by looking into the java implmentation

    timestamp       1545905337
    httpMethod      POST
    normalizedUrl   https://sociallize.us1.gigya.com/socialize.getSDKConfig
    urlparams       ApiKey%3DsomeApiKey%26nonce%3D1545905337000_1%26timestamp%3D1545905337
    baseSignature   POST&https%3A%2F%2Fsociallize.us1.gigya.com%2Fsocialize.getSDKConfig&ApiKey%3DsomeApiKey%26nonce%3D1545905337000_1%26timestamp%3D1545905337
    secret          asda34asfasfj9fuas
    signature       nC69hzGbTdPW3WlUl6k0ZeCd0CY=

    ==== SHOULD BE =====
    timestamp       1545905337
    nonce           1545905337000_1
    signature       nC69hzGbTdPW3WlUl6k0ZeCd0CY=
    """

    params = {
    "ApiKey": "someApiKey",
    "nonce": "1545905337000_1",
    "timestamp": "1545905337",
    }

    session_secret = base64.b64encode(binascii.unhexlify("6ac75adf86ac7dab1f8fd7ee6a")).decode("utf-8")
    print(session_secret)

    sig = gigya_sign(session_secret, "POST", "https://sociallize.us1.gigya.com/socialize.getSDKConfig", params)

    print(sig)
    print("nC69hzGbTdPW3WlUl6k0ZeCd0CY")
        
def gigya_nonce():
    return str(round(time.time() * 1000)) + "_-" + str(random.randint(100000000, 999999999))

def gigya_print_http(r):
    """
    print(" < " + str(r.request.method) + " " + r.request.url)
    for k in r.request.headers:
        print(" < " + k + ": " + r.request.headers[k])
    if r.request.body:
        print()
        print(r.request.body)
    print()

    print(" > " + "HTTP " + str(r.status_code) + " " + r.reason)
    for k in r.headers:
        print(" > " + k + ": " + r.headers[k])
    if r.text:
        print()
        print(r.text)
    print()
    """
    return

def gigya_login(email, password, gigya_apikey, gigya_domain):

    gigya_useragent = "okhttp/4.10.0"

    r = do_http("POST", "https://socialize." + gigya_domain + "/socialize.getIDs", headers={
        "apikey": gigya_apikey,
        "user-agent": gigya_useragent,
        "content-type": "application/x-www-form-urlencoded"
    }, data={
        "apiKey": gigya_apikey,
        "format": "json",
        "httpStatusCodes": "false",
        "nonce": gigya_nonce(),
        "sdk": "Android_7.0.11",
        "targetEnv": "mobile"
    })

    gigya_print_http(r)
    r.raise_for_status()

    data = r.json()

    gigya_ucid = data["ucid"]
    gigya_gmid = data["gmid"]
    gigya_gcid = data["gcid"]

    r = do_http("POST", "https://accounts." + gigya_domain + "/accounts.login", headers={
        "apikey": gigya_apikey,
        "user-agent": gigya_useragent,
        "content-type": "application/x-www-form-urlencoded"
    }, data={
        "apiKey": gigya_apikey,
        "format": "json",
        "httpStatusCodes": "false",
        "nonce": gigya_nonce(),
        "sdk": "Android_7.0.11",
        "targetEnv": "mobile",

        "gmid": gigya_gmid,
        "ucid": gigya_ucid,

        "loginID": email,
        "password": password
    })
    gigya_print_http(r)
    r.raise_for_status()

    data = r.json()

    gigya_country = data["profile"]["country"]
    gigya_sig_timestamp = data["signatureTimestamp"]
    gigya_session_token = data["sessionInfo"]["sessionToken"]
    gigya_session_secret = data["sessionInfo"]["sessionSecret"]

    params = {
        "apiKey": gigya_apikey,
        "fields": "country",
        "format": "json",
        "gmid": gigya_gmid,
        "httpStatusCodes": "false",
        "nonce": gigya_nonce(),
        "oauth_token": gigya_session_token,
        "sdk": "Android_7.0.11",
        "targetEnv": "mobile",
        "timestamp": gigya_sig_timestamp,
        "ucid": gigya_ucid
    }

    url = "https://accounts." + gigya_domain + "/accounts.getJWT"
    params["sig"] = gigya_sign(gigya_session_secret, "POST", url, params)

    r = do_http("POST", url, headers={
        "apikey": gigya_apikey,
        "user-agent": gigya_useragent,
        "content-type": "application/x-www-form-urlencoded"
    }, data=params)
    gigya_print_http(r)
    r.raise_for_status()

    data = r.json()

    return data["id_token"], gigya_country
