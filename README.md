SteemDNS
=======
This script was built for SteemDNS, a decentralized DNS system running on the Steem Blockchain. 

Created by [@Someguy123 (Steemit Link)](https://steemit.com/@someguy123) or Someguy123 on Github.

At the current point in time, some of these commands are not working. The most important commands work, which are `rescan_users`, `scan_user`, `store_domain`, and `watch_chain`.
    
    Usage: python3 cmd.py [cmd] [args]

    Commands:
    store_domain domain records(JSON) - Add a domain manually
    rescan_since blknumber - Rescan everything after this block
    rescan_users - Rescan all users
    scan_user username addtodb(BOOL) - Scans a user and returns their metadata. Can add to DB too
    watch_chain - Monitors the blockchain and adds to db


License
======
GNU Affero GPL - check LICENSE for more information.

tl;dr; - if you make any changes to this project, you need to contribute them back, even if you don't redistribute the code in any format, and are expected to inform people using your DNS service that the code was taken from here.


Installing
========
The SteemDNS script depends on Python 3, and the Piston python API.

Install PowerDNS (stable, NOT MASTER): [PowerDNS Repo Site](https://repo.powerdns.com/)

Install the `gsqlite3` backend for PowerDNS (it will be in your repos after you set up the powerdns repo)

If you're using Ubuntu 16.04 the instructions are as follows:

    sudo su
    echo "deb http://repo.powerdns.com/ubuntu xenial-rec-40 main" > /etc/apt/preferences.d/pdns.list
    echo -e "Package: pdns-*\nPin: origin repo.powerdns.com\nPin-Priority: 600" > /etc/apt/preferences.d/pdns
    curl https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add -
    apt update && apt install pdns-recursor pdns-backend-sqlite3


Edit /etc/powerdns/pdns.conf and add the following under where the existing `launch=` is (replace it).

    launch=gsqlite3
    gsqlite3-database=/var/spool/powerdns/steem.sqlite

You may want to add a recursive resolver (this allows you to resolve non-steem domains like google.com):

    recursor=8.8.4.4

Simply run the following command to install dependencies:

    pip3 install -r requirements.txt

Create a DB using

    sudo touch /var/spool/powerdns/steem.sqlite
    sudo sqlite3 /var/spool/powerdns/steem.sqlite < schema.sql
    # to allow access by different users, i.e. the one running the watcher
    sudo chmod 777 /var/spool/powerdns/steem.sqlite

You'll need to configure the nameserver domain (which is a domain you own that points at your server), and SOA in the python file:

    NAMESERVERS = ['ns1.example.com']
    SOA = 'ns1.example.com dns-admin.example.com 0'

If you're running this locally, and aren't going to be publishing your DNS, you can set all domains to `localhost`. Leave the '0' at the end of the SOA. That tells PowerDNS to automatically detect when a domain changes and adjust the value automatically.

Now re-scan all users (may take a long time!)

    python3 cmd.py rescan_users

Once it's re-scanned, you can now run the watcher command. Run this in screen to prevent it from closing when you disconnect.

    screen -S steemwatchchain python3 cmd.py watch_chain

You can inspect the sqlite database by running `sqlite3 /var/spool/powerdns/steem.sqlite`. To verify if your DNS is working, just run on the server:

    dig a someguy123.steem @127.0.0.1

If this is public, remember to verify the outside can see it too!

At this point you should be good to go. Keep an eye on the steem watch script in-case it crashes (though it should be reliable), you may want to test it by publishing your own DNS records to your json_metadata.