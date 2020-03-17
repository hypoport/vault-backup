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

# looks at an argument for a value and prints the key
#  if a value exists
# def recurse_for_values(path_prefix, candidate_key):
#     candidate_values = candidate_key['data']['keys']
#     for candidate_value in candidate_values:
#         next_index = path_prefix + candidate_value
#         if candidate_value.endswith('/'):
#             next_value = client.list(next_index)
#             recurse_for_values(next_index, next_value)
#         else:
#             stripped_prefix=path_prefix[:-1]
#             final_dict = client.read(next_index)['data']
#             print ("\nvault write {}".format(next_index), end='')

#             sorted_final_keys = sorted(final_dict.keys())
#             for final_key in sorted_final_keys:
#                 final_value = final_dict[final_key]
#                 try:
#                     final_value = final_value.encode("utf-8")
#                 except AttributeError:
#                     final_value = final_value
#                 print (" {0}={1}".format(final_key, repr(final_value)), end='')


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

    if version == 1:
        print("Not supported yet...")
    elif version == 2:
        try:
            list_response = client.secrets.kv.v2.list_secrets(
                mount_point = mount,
                path = path
            )
            print(list_response)
        except hvac.exceptions.InvalidPath:
            print("No Secrets found in mount {} and path {}".format(mount,path))
        


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
