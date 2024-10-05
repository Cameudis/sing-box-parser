#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import cloudscraper
import json

# -*- Config -*-

# sing-box configuration
subscribe_url = ""

def fetch(url):
    scraper = cloudscraper.create_scraper()
    return scraper.get(url).text

def parser(data):
    # -*- dns setting -*-
    data['dns']['final'] = 'local'
    data['dns']['servers'].append({
        "tag" : "google",
        "address" : "tls://8.8.8.8",
    })
    for server in data['dns']['servers']:
        if server['tag'] == 'local':
            server['address'] = '223.5.5.5'
    for rule in data['dns']['rules']:
        if 'invert' in rule and 'geosite' in rule and rule['geosite'] == 'cn':
            rule['server'] = 'google'

    # -*- outbounds setting -*-
    data['outbounds'].append({
        "tag" : "fudan-http",
        "type" : "http",
        "server" : "127.0.0.1",
        "server_port" : 8888,
    })
    data['outbounds'].append({
        "tag" : "fudan-socks",
        "type" : "socks",
        "server" : "127.0.0.1",
        "server_port" : 1080,
    })
    for outbound in data['outbounds']:
        if outbound['tag'] == 'Manually':
            outbound['default'] = 'direct'
        if outbound['tag'] == 'Scholar':
            outbound['outbounds'].insert(0, "auto-tw")
            outbound['default'] = "auto-tw"

    # -*- ntp setting -*-
    data['ntp'] = {
        "enabled" : True,
        "server" : "ntp.sjtu.edu.cn",
    }

    # -*- rule setting -*-
    # tencent tracking
    data['route']['rules'].insert(1, {
        "domain" : ["otheve.beacon.qq.com"],
        "outbound" : "block",
    })
    # fudan easyconnect
    data['route']['rules'].insert(1, {
        "domain_suffix" : [".fudan.edu.cn"],
        "outbound" : "fudan-http",
    })
    data['route']['rules'].insert(1, {
        "ip_cidr" : ["10.0.0.0/8"],
        "outbound" : "fudan-socks",
    })
    # ssh
    for rule in data['route']['rules']:
        if 'port' in rule and 22 in rule['port']:
            rule['outbound'] = 'direct'

    return data

if __name__ == '__main__':
    raw = fetch(subscribe_url)
    data = parser(json.loads(raw))

    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)
