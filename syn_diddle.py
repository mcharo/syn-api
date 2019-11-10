#!/usr/bin/env python3
import requests
import argparse
import json
from getpass import getpass

class SynologyAuth:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = 'http://%s:%s/webapi/' % (self.host, self.port)
        self.application = 'Core'
        self.session_expire = True
        self.sid = None

    def login(self):
        login_api = 'auth.cgi?api=SYNO.API.Auth'
        param = {'version': '2', 'method': 'login', 'account': self.username,
                    'passwd': self.password, 'session': self.application, 'format': 'cookie'}

        if not self.session_expire:
            if self.sid is not None:
                self.session_expire = False
        else:
            session_request = requests.get(self.base_url + login_api, param)
            self.sid = session_request.json()['data']['sid']
            self.session_expire = False

class SynologyCore:
    def __init__(self, auth):
        self.auth = auth

    def get_syno_api_url(self, api_name):
        query_path = 'query.cgi?api=SYNO.API.Info'
        list_query = {'version': '1', 'method': 'query', 'query': 'all'}

        response = requests.get(self.auth.base_url + query_path, list_query).json()['data']
        if api_name in response:
            api_path = response[api_name]['path']
            return ('%s%s' % (self.auth.base_url, api_path)) + '?api=' + api_name


    def create_syno_letsencrypt(self, desc, domain_names, email, as_default=False):
        api_name = 'SYNO.Core.Certificate.LetsEncrypt'
        domains = []
        domains.append(domain_names)
        req_params = {
            'method': 'create',
            'version': '1',
            'timeout': 360000,
            '_sid': self.auth.sid,
            'params': {
                'desc': desc,
                'as_default': str(as_default).lower(),
                'domain_name': ';'.join(domains),
                'email': email
            }
        }
        url = self.get_syno_api_url(api_name)
        #response = requests.get(url, req_params)
        return {
            'url': url,
            'params': req_params
        }

    def list_syno_letsencrypt(self):
        api_name = 'SYNO.Core.Certificate.LetsEncrypt.Account'
        req_params = {
            'method': 'list',
            'version': '1',
            '_sid': self.auth.sid
        }
        url = self.get_syno_api_url(api_name)
        response = requests.get(url, req_params)
        return json.loads(response.content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip_address", required=True)
    parser.add_argument("-p", "--port", default='5000')
    parser.add_argument("-u", "--user", required=True)
    args = parser.parse_args()
    
    password = getpass(prompt=f"Enter Synology password for {args.user}: ")
    
    auth = SynologyAuth(args.ip_address, args.port, args.user, password)
    auth.login()

    core = SynologyCore(auth)
    print(core.list_syno_letsencrypt().get('data'))