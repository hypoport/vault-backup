#! /usr/bin/env python
#
# Dumps a HashiCorp Vault database to write statements.
# Useful for backing up in-memory vault data
# and later restoring from the generated script.
#
# Requires: an already-authenticated session
#
# Reads env vars:
# - VAULT_ADDR  which points to desired Hashicorp Vault instance, default http://localhost:8200
# - TOP_VAULT_PREFIX to specify path to dump, for partial backups, default /secret/
#
# Use custom encoding:
#   PYTHONIOENCODING=utf-8 python vault-dump.py
#
# Copyright (c) 2017 Shane Ramey <shane.ramey@gmail.com>
# Licensed under the Apache License, Version 2.0

import sys
import os
import hvac
import datetime
from shlex import quote

def print_header():
    date = "{} UTC".format(datetime.datetime.utcnow())
    vault_address = os.environ.get('VAULT_ADDR')

    print ('#')
    print ('# vault-dump.py backup')
    print ("# backup date: {}".format(date))
    print ("# VAULT_ADDR env variable: {}".format(vault_address))
    print ('# STDIN encoding: {}'.format(sys.stdin.encoding))
    print ('# STDOUT encoding: {}'.format(sys.stdout.encoding))
    print ('#')
    print ('# WARNING: not guaranteed to be consistent!')
    print ('#')


def get_kv_engines():
    secret_engines = client.sys.list_mounted_secrets_engines()['data']
    kv_engines = [
        {
            "path": path,
            "version": int(secret_engine["options"]["version"])
        } 
        for path, secret_engine in secret_engines.items() 
        if secret_engine["type"] == "kv"
    ]
    return kv_engines

def recurse_for_values(mount, version, path):

    if version == 2:
        try:
            
            list_response = client.secrets.kv.v2.list_secrets(
                mount_point = mount,
                path = path
            )
            
            candidate_values = list_response['data']['keys']
            
            for candidate_value in candidate_values:
                if candidate_value.endswith('/'):
                    recurse_for_values(mount, version, path+candidate_value)
                else:
                    full_path = mount+path[1:]+candidate_value
                    secret = client.secrets.kv.v2.read_secret_version(
                        mount_point = mount,
                        path=path[1:]+candidate_value,
                    )
                    vault_command = "vault kv put {}".format(full_path)
                    for key, value in secret["data"]["data"].items():
                        vault_command += " {}={}".format(key,quote(value))
                    
                    print(vault_command)

        except hvac.exceptions.InvalidPath:
            print("# No Secrets found in mount {} and path {}".format(mount,path))
    
    else:
        print("# v1 not supported right now...")
        


hvac_url = os.environ.get('VAULT_ADDR','http://localhost:8200')
hvac_token = os.environ.get('VAULT_TOKEN','http://localhost:8200')

hvac_client = {
    'url': hvac_url,
    'token': hvac_token,
}
client = hvac.Client(**hvac_client)
assert client.is_authenticated()

kv_engines = get_kv_engines()

print_header()

for kv_engine in kv_engines:
    recurse_for_values(kv_engine["path"], kv_engine["version"], "/")
