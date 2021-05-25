import json
import time

import requests as req

from datetime import datetime, timezone

import calendar

import os.path

import sys


def write_csv(file: str, message_report: list):
    try:
        table = open(file, 'w')
        for line_report in message_report:
            table.write(';'.join(line_report) + '\n')
    except Exception:
        time.sleep(10)
        table = open(file, 'w')
        for line_report in message_report:
            table.write(';'.join(line_report) + '\n')
    table.close()


now = datetime.now(timezone.utc)

months = ['january', 'february', 'march', 'april',
          'may', 'june', 'july', 'august', 'september',
          'october', 'november', 'december']
day = now.day
year = now.year
month = now.month

new_month_flag = False
if not os.path.exists(str(year)):
    year -= 1
    month = 12
    new_month_flag = True
if not os.path.exists(str(year) + '/' + months[month - 1]):
    month -= 1
    new_month_flag = True

file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + months[month - 1] + '_' + str(year) + '.csv'

table_csv = []

if not os.path.exists(file_name):
    data = open(file_name, 'w')
    start = 'Start time:;' + str(day) + '.' + str(months[now.month]) + '.' + str(year)
    end = 'End time:;' + str(calendar.monthrange(year, month)[1]) + '.' + months[now.month] + '.' + str(year)
    data.write(start + '\n')
    data.write(end + '\n')
    data.write('event_timestamp;notification_timestamp;online_time;notification_profile;charging_station_name;'
               'charging_station_id;event_type;error_code;notification_message' + '\n')
    data.close()
else:
    reports = open(file_name, 'r')
    for line in reports:
        table_csv.append(line[:-1].split(';'))
header = table_csv[:3]
data = table_csv[3:]

s_id = open('Station_ID.csv', 'r')
stations = [x[:-1] for x in s_id]
s_id.close()

station_ids = {x.split(';')[0]: x.split(';')[1] for x in stations[1:]}

try:
    api = sys.argv[1]
except IndexError as err:
    print('You must lunch with your api key for example:'
          '"py add_offline.py asdfasdfadfa" where "asdfasdfadfa" is api key'
          )
    exit()

new_month_table = []

for line in data:
    if line[-1] == '':
        station_id = line[4].upper()
        eventstamp = datetime.strptime(line[0][:19], '%Y-%m-%dT%H:%M:%S')
        try:
            url = 'https://cd-hub-gw.tingcore-infra.com/v1/charging-stations/' + station_ids[station_id] + ':dynamic'
            response = req.request('GET', url, headers={
                'Accept': 'application/json',
                'x-api-key': api
            }, verify=False
                                   )

            resp_json = json.loads(response.text)
            status = resp_json['status']
            connectorStatuses = set()
            for connector in resp_json['connectorStatuses']:
                connectorStatuses.add(connector['connectorStatus']['status'])
            print(station_id)
            print(connectorStatuses)
            print(status)

            lastupdate = datetime.strptime(
                resp_json['connectorStatuses'][0]['connectorStatus']['lastUpdated'][:19], '%Y-%m-%dT%H:%M:%S')

            if status == 'ONLINE' and (('AVAILABLE' in connectorStatuses) or ('OCCUPIED' in connectorStatuses)):
                line[-1] = str(lastupdate - eventstamp)
            elif new_month_flag:
                line[-1] = str(now - lastupdate)
                new_month_table.append(line)
            else:
                pass
        except Exception as err:
            print(err)
            line[-1] = 'Station not found'

table_csv = header + data

write_csv(file_name, table_csv)

if new_month_flag:
    year = now.year
    month = now.month
    file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + months[month - 1] + '_' + str(year) + '.csv'
    start = ['Start time:', str(day) + '.' + str(months[month - 1]) + '.' + str(year)]
    end = ['End time:', str(calendar.monthrange(year, month)[1]) + '.' + months[month - 1] + '.' + str(year)]
    table_csv = [start, end] + new_month_table
    write_csv(file_name, table_csv)
