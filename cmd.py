#!/usr/bin/env python3
#
# SteemDNS Import Script for PowerDNS (SQLite)
#
# Released by Someguy123 (https://www.someguy123.com)
# License: GNU Affero GPL
# Project URL: https://github.com/Someguy123/steemdns
#

import sqlite3
import sys
import json
from piston.steem import Steem

NAMESERVERS = ['ns1.example.com']
SOA = 'ns1.example.com dns-admin.example.com 0'

conn = sqlite3.connect('/var/spool/powerdns/steem.sqlite')
c = conn.cursor()

steem = Steem(node="wss://node.steem.ws")
rpc = steem.rpc

class SteemDNS:
    def load_accounts(self):
        users = rpc.lookup_accounts(-1, 10000)
        more = True
        while more:
            print("Chunking {}".format(len(users)))
            newUsers = rpc.lookup_accounts(users[-1], 10000)
            if len(newUsers) < 10000:
                more = False
            users = users + newUsers
        return users

    def watch_chain(self):
        for data in rpc.stream('account_update'):
            if 'json_metadata' in data and data['json_metadata'] != '':
                try:
                    records = json.loads(data['json_metadata'])
                    if 'dns' in records:
                        records = records['dns']['records']
                        account = data['account']
                        self.store_domain(account+".steem", records)
                except Exception as e:
                    print('error parsing data: {}'.format(data))
                    print('exception was {}'.format(e))
                    pass
        return
    def rescan_users(self):
        accounts = self.scan_accounts()

        for a in accounts:
            self.scan_user(a, True)
    def scan_user(self, username, add=False):
        data = rpc.get_account(username)
        j = data['json_metadata']
        if j != '' and j != '{}':
            try:
                obj = json.loads(j)
                print(obj)
                if 'dns' not in obj or 'records' not in obj['dns']:
                    return None
                print(username + ' : ' + j)
                if add:
                    self.store_domain(username+'.steem', obj['dns']['records'])
            except:
                pass
            return obj
    def rescan_since(self, start_block):
        return
    def store_domain(self, domain, records = None):
        #domain = sys.argv[1]
        #records = None

        # iterate records
        try:
            if type(records) is str:
                records = json.loads(records)
        except:
            print('error parsing records')
            return

        sel = c.execute('SELECT id FROM domains WHERE name = ?', (domain,))
        domain_id = c.fetchone()
        print('Locating domain...')
        # Domain isn't found. Create the record
        if domain_id is None:
            print('Domain not found. Creating')
            c.execute("INSERT INTO domains (name,type) VALUES (?,'NATIVE')", (domain,))
            domain_id = c.lastrowid
            # SOA Record
            c.execute("INSERT INTO records (domain_id, name, content, type, ttl, prio) values (?,?,?,?,?,?) ", (domain_id, domain, SOA, 'SOA', 86400, None,));
            for ns in NAMESERVERS:
                c.execute("INSERT INTO records (domain_id, name, content, type, ttl, prio) values (?,?,?,?,?,?) ", (domain_id, domain, ns, 'NS', 86400, None,));
        else:
            domain_id = domain_id[0]

        if records is None:
            print('No records. Giving up.')
            return

        c.execute("DELETE FROM records WHERE domain_id = ? AND type IN ('A', 'CNAME', 'TXT', 'SPF', 'MX')", (domain_id,))
        print('Deleted records')
        for r in records:
            if type(r) is not list:
                print('[ERR] not a list')
                continue
            if len(r) < 3:
                print('[ERR] < 3 items. Data: {}'.format(r))
                continue
            if r[1] not in ['A', 'CNAME', 'TXT', 'SPF', 'MX']:
                print('[ERR] invalid record type {}'.format(r[1]))
                continue
            prio = None
            if r[1] is 'MX':
                if len(r) != 4:
                    prio = 10
                else:
                    prio = r[3]
            subdomain = domain
            if r[0] != '@' and r[0] != '':
                subdomain = r[0] + "." + domain
            print(type(domain_id))
            domain_id = int(domain_id)
            c.execute("INSERT INTO records (domain_id, name, content, type, ttl, prio) values (?,?,?,?,?,?) ", (domain_id, subdomain, r[2], r[1], 600, prio));
            print('Added record {} with content {} for domain {}'.format(r[1], r[2], r[0]))
            conn.commit()

if __name__ == "__main__":
    s = SteemDNS()
    helptext = """
    Usage: {} [cmd] [args]

    Commands:
    store_domain domain records(JSON) - Add a domain manually
    rescan_since blknumber - Rescan everything after this block
    rescan_users - Rescan all users
    scan_user username addtodb(BOOL) - Scans a user and returns their metadata. Can add to DB too
    watch_chain - Monitors the blockchain and adds to db

    """
    if len(sys.argv) < 2:
        print(helptext.format(sys.argv[0]))
    a = sys.argv
    if a[1] == 'rescan_users':
        s.rescan_users()
        exit()
    if a[1] == 'watch_chain':
        s.watch_chain()
        exit()
    if a[1] == 'scan_user' and len(a) == 4:
        s.scan_user(a[2], bool(a[3]))
        exit()

    print(helptext.format(sys.argv[0]))
