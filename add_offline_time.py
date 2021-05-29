import json
import time
import requests as req
from datetime import datetime, timezone
import calendar
import os.path
from tokens import token_api


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

def get_json_text(id):
    url = 'https://cd-hub-gw.tingcore-infra.com/v1/charging-stations/' + id + ':dynamic'
    response = req.request('GET', url, headers={
        'Accept': 'application/json',
        'x-api-key': token_api
    }, verify=False
                             )

    resp_json = json.loads(response.text)
    try:
        statuses = resp_json['connectorStatuses']
    except Exception as err:
        print(err)
        return 'Station not found'
    return resp_json

def get_time_offline(data, new_month_flag, new_month_table, station_ids):
    for line in data:
        if line[-1] == '':
            station_id = line[4].upper()
            eventstamp = datetime.strptime(line[0][:19], '%Y-%m-%dT%H:%M:%S')
            resp_json = get_json_text(station_ids[
                    station_id])
            if resp_json != 'Station not found':
                status = resp_json['status']
                statuses = resp_json['connectorStatuses']
            else:
                line[-1] = resp_json
                continue
            connectorStatuses = []
            connectors = 0
            for connector_num in range(len(statuses)):
                connectorStatuses.append(statuses[connector_num]['connectorStatus']['status'])
                if statuses[connector_num]['connectorStatus']['status'] in ('OCCUPIED', 'AVAILABLE'):
                    connectors = connector_num

            lastupdate = datetime.strptime(
                statuses[connectors]['connectorStatus']['lastUpdated'][:19], '%Y-%m-%dT%H:%M:%S')

            if status == 'ONLINE' and (('AVAILABLE' in connectorStatuses) or ('OCCUPIED' in connectorStatuses)):
                line[-1] = str(lastupdate - eventstamp)
            elif new_month_flag:
                new_month_table.append(line)
                line[0] = str(now)[0:10] + 'T' + str(now)[12:19] + 'Z'
                line[-1] = str(now - lastupdate)
    return data, new_month_table


def create_new_csv(now, months, new_month_table):
    year = now.year
    month = now.month
    file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + months[month - 1] + '_' + str(year) + '.csv'
    start = ['Start time:', str(day) + '.' + str(months[month - 1]) + '.' + str(year)]
    end = ['End time:', str(calendar.monthrange(year, month)[1]) + '.' + months[month - 1] + '.' + str(year)]
    table_csv = [start, end] + new_month_table
    write_csv(file_name, table_csv)

now = datetime.now(timezone.utc)


last_day = 31

now = datetime.now(timezone.utc)

months = ['january', 'february', 'march', 'april',
          'may', 'june', 'july', 'august', 'september',
          'october', 'november', 'december']
day = now.day
year = now.year
month = now.month

new_month_flag = False
if not os.path.exists(str(year)):
    os.mkdir(year)
    os.mkdir(year + '/' + month)
    year -= 1
    month = 12
    new_month_flag = True
if not os.path.exists(str(year) + '/' + months[month - 1]):
    os.mkdir(year + '/' + month)
    month -= 1
    new_month_flag = True

file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + months[month - 1] + '_' + str(year) + '.csv'

table_csv = []

if not os.path.exists(file_name):
    print(f'No file {file_name} you must launch first main.py')
    exit()
else:
    reports = open(file_name, 'r')
    for line in reports:
        table_csv.append(line[:-1].split(';'))
    header = table_csv[:3]
    data = table_csv[3:]

s_id = open('Station_ID.csv', 'r')
stations = {x[:-1].split(';')[0]: x[:-1].split(';')[1] for x in s_id}
s_id.close()

new_month_table = []

data, new_month_table = get_time_offline(data, new_month_flag, new_month_table, stations)

table_csv = header + data

write_csv(file_name, table_csv)

if new_month_flag:
    create_new_csv(now, months, new_month_table)
