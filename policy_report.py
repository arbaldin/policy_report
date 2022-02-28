#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
import json
import re
import requests
import urllib.parse

from getpass import getpass


def load_config(base_url, node):
    node_info = json.loads(
        requests.get("{0}/show/{1}?format=json".format(
            base_url, node), auth=(ADUser, ADPass)).text)
    node_config_url = "{0}/fetch/{1}".format(base_url,
                                             urllib.parse.quote(
                                                 node_info[
                                                     "full_name"]))
    node_config = requests.get(node_config_url, auth=(ADUser,
                                                 ADPass)).text.splitlines()
    return(node_config)


ADUser = input("Usuario do AD: ")
TVTUser = input("Usuario tvt: ")
ADPass = getpass("Senha do AD: ")

base_url = "http://your.oxidized.url/node"

currentDT = datetime.datetime.now()

with open("devices.list", "r") as nodes:
    node_list = [node.strip() for node in nodes]

for node in node_list:
    node_config = load_config(base_url, node)
    j = 0
    while j < len(node_config):
        
        if re.match("^policy-map", node_config[j]):
            policy_name = re.search("policy-map.(.*)", node_config[j]).group(1)
            while node_config[j + 1].startswith(" ") is True:
                j += 1
                if re.match("\s+police", node_config[j]):
                    policy_bandwidth = re.search(".+police.(.+?)\s",
                                                 node_config[j]).group(1)
                    policy_unit = re.search(".+police.(.+?)\s(.+?)\s",
                                            node_config[j]).group(2)
                    if "bps" not in policy_unit:
                        policy_unit = "bps"
            policy = [policy_name, " ".join([policy_bandwidth, policy_unit])]
            try:
                all_policys.append(policy)
            except:
                all_policys = [policy]
            try:
                node_policys[node] = dict(all_policys)
            except:
                node_policys = {node: dict(all_policys)}

        if re.match("^interface .*[e|E]thernet.*\d+\/\d+", node_config[j]):
            int_name = re.search("^interface.(.*)", node_config[j]).group(1)
            int_desc = "---"
            int_policy_in = "---"
            int_policy_out = "---"
            while node_config[j + 1].startswith(" ") is True:
                j += 1
                if re.match(".description.(.*)", node_config[j]):
                    int_desc = re.search(".description.(.*)",
                                     node_config[j]).group(1)
                elif re.match(".port-name.(.*)", node_config[j]):
                    int_desc = re.search(".port-name.(.*)", node_config[j]).group(1)
                elif re.match(".service-policy input.(.*)", node_config[j]):
                    int_policy_in = re.search(".service-policy input.(.*)",
                                          node_config[j]).group(1)
                elif re.match(".rate-limit input policy-map.(.*)", node_config[j]):
                    int_policy_in = re.search(".rate-limit input policy-map.("
                                           ".*)", node_config[j]).group(1)
                elif re.match(".service-policy output.(.*)", node_config[j]):
                    int_policy_out = re.search(".service-policy output.("
                                           ".*)", node_config[j]).group(1)
                elif re.match(".rate-limit output policy-map.(.*)", node_config[j]):
                    int_policy_in = re.search(".rate-limit output policy-map.("
                                           ".*)", node_config[j]).group(1)
            interface = [int_name, [int_desc, int_policy_in, int_policy_out]]
            try:
                all_interfaces.append(interface)
            except:
                all_interfaces = [interface]
            try:
                node_interfaces[node] = dict(all_interfaces)
            except:
                node_interfaces = {node: dict(all_interfaces)}

        j += 1
    all_policys = ""
    all_interfaces = ""

    for interface in node_interfaces[node]:
        if node_interfaces[node][interface][1] != "---":
            policy_in_band = node_policys[node][node_interfaces[node][interface][1]]
        else:
            policy_in_band = "ND"
        if node_interfaces[node][interface][2] != "---":
            policy_out_band = node_policys[node][node_interfaces[node][interface][2]]
        else:
            policy_out_band = "ND"
        try:
            rows.append([node, interface, node_interfaces[node][interface][0], node_interfaces[node][interface][1], policy_in_band, node_interfaces[node][interface][2], policy_out_band])
        except:
            rows = [[node, interface, node_interfaces[node][interface][0], node_interfaces[node][interface][1], policy_in_band, node_interfaces[node][interface][2], policy_out_band]]

with open("".join([currentDT.strftime("%Y%m%d-%H%M%S"), ".csv"]), "w") as policy_report:
    writer = csv.writer(policy_report)
    writer.writerows(rows)