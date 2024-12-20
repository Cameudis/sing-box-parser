#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import cloudscraper
import json
import yaml

# -*- Config -*-

# sing-box configuration
subscribe_url = "https://update.glados-config.com/singbox/481162/bc83b20f23b9eeb5"
clash_subscribe_url = "https://update.glados-config.com/clash/481162/4e8de2a/195828/glados.yaml"

def fetch(url):
    scraper = cloudscraper.create_scraper()
    return scraper.get(url).text

def parser(data, clash_config):
    # -*- dns setting -*-
    data['dns']['final'] = 'local'
    data['dns']['servers'].append({
        "tag" : "google",
        "address" : "tls://8.8.8.8",
    })
    for server in data['dns']['servers']:
        if server['tag'] == 'local':
            server['address'] = '119.29.29.29'
    for rule in data['dns']['rules']:
        if 'invert' in rule and 'geosite' in rule and rule['geosite'] == 'cn':
            rule['server'] = 'google'

    # -*- inbounds setting -*-
    data['inbounds'] = [{
        "type": "mixed",
        "tag": "mixed-in",
          
        "listen": "::",
        "listen_port": 2337,
          
        "users": [],
        "set_system_proxy": False
    }]

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
            outbound['outbounds'].insert(0, "auto-uk")
            outbound['outbounds'].insert(0, "auto-tw")
            outbound['default'] = "auto-uk"
    # migrate US and JP outbounds from clash config
    us_outbounds = []
    jp_outbounds = []
    for p in clash_config['proxies']:
        if 'US' in p['name'] or 'JP' in p['name']:
            assert p['plugin'] == 'obfs'
            data['outbounds'].append({
                "tag" : p['name'],
                "server" : p['server'],
                "server_port" : p['port'],
                "method" : p['cipher'],
                "password" : p['password'],
                "udp_over_tcp": True,
                "plugin": "obfs-local",
                "type" : 'shadowsocks',
                "plugin_opts": f"obfs={p['plugin-opts']['mode']};obfs-host={p['plugin-opts']['host']}"
            })
            if 'US' in p['name']:
                us_outbounds.append(p['name'])
            if 'JP' in p['name']:
                jp_outbounds.append(p['name'])
    data['outbounds'].append({
        "type": "urltest",
        "tag": "auto-us",
        "outbounds": us_outbounds,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "3m",
        "tolerance": 50
    })
    data['outbounds'].append({
        "type": "urltest",
        "tag": "auto-jp",
        "outbounds": jp_outbounds,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "3m",
        "tolerance": 50
    })

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
        "domain_suffix" : [".fudan.edu.cn",".fducslg.com"],
        "outbound" : "fudan-http",
    })
    data['route']['rules'].insert(1, {
        "ip_cidr" : ["10.0.0.0/8"],
        "outbound" : "fudan-socks",
    })
    data['route']['rules'].insert(1, {
        "domain" : ["stuvpn.fudan.edu.cn"],
        "outbound" : "direct",
    })
    # gossip infrastructure
    data['route']['rules'].insert(1, {
        "domain_suffix" : [".gossip.team"],
        "outbound" : "direct",
    })
    # Google (NotebookLM, Learn About)
    data['route']['rules'].insert(1, {
        "domain_suffix" : [".google", ".google.com", ".withgoogle.com"],
        "outbound" : "auto-us",
    })
    # ssh
    for rule in data['route']['rules']:
        if 'port' in rule and 22 in rule['port']:
            rule['outbound'] = 'direct'

    return data

if __name__ == '__main__':
    raw = json.loads(fetch(subscribe_url))
    clash_config = yaml.load(fetch(clash_subscribe_url), Loader=yaml.FullLoader)
    data = parser(raw, clash_config)

    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)
