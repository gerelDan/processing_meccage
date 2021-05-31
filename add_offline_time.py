import json
import time
import requests as req
from datetime import datetime, timezone
import calendar
import os.path
from tokens import token_api
from main import directory_year, directory_month


def write_csv(file: str, message_report: list):
    """
    this function write csv file and if this file is busy then function waiting 10 seconds
    :param file: str
    :param message_report: list
    :return:
    """
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


def get_json_text(id_st):
    """
    this function get data from site via api
    :param id_st: str
    :return: dict or 'Station not found'
    """
    url = 'https://cd-hub-gw.tingcore-infra.com/v1/charging-stations/' + id_st + ':dynamic'
    response = req.request('GET', url, headers={
        'Accept': 'application/json',
        'x-api-key': token_api
    }, verify=False
                           )

    resp_json = json.loads(response.text)
    print(resp_json)
    if len(resp_json) == 4:
        return resp_json
    else:
        print('Station not found')
        return 'Station not found'


def get_time_offline(data_list: list, new_month_flag: bool, new_month_table: list, station_ids: dict):
    """
    this function take last update status connector
    :param data_list: list
    :param new_month_flag: bool
    :param new_month_table: list
    :param station_ids: dict
    :return: list, list
    """

    for line in data_list:
        if line[-1] == '':
            station_id = line[4].upper()
            event_time_stamp = datetime.strptime(line[0][:19], '%Y-%m-%dT%H:%M:%S')
            resp_json = get_json_text(station_ids[
                                          station_id])
            if resp_json != 'Station not found':
                status = resp_json['status']
                statuses = resp_json['connectorStatuses']
            else:
                line[-1] = resp_json
                continue
            connector_statuses = []
            connectors = 0
            for connector_num in range(len(statuses)):
                connector_statuses.append(statuses[connector_num]['connectorStatus']['status'])
                if statuses[connector_num]['connectorStatus']['status'] in ('OCCUPIED', 'AVAILABLE'):
                    connectors = connector_num

            last_update = datetime.strptime(
                statuses[connectors]['connectorStatus']['lastUpdated'][:19], '%Y-%m-%dT%H:%M:%S')

            if status == 'ONLINE' and (('AVAILABLE' in connector_statuses) or ('OCCUPIED' in connector_statuses)):
                line[-1] = str(last_update - event_time_stamp)
            elif new_month_flag:
                new_month_table.append(line)
                line[0] = str(now)[0:10] + 'T' + str(now)[12:19] + 'Z'
                line[-1] = str(now - last_update)
    return data_list, new_month_table


def create_new_csv(now, months_name_list: list, new_month_table: list):
    """
    This function create new csv file with incomplete data from last month
    :param now: data time
    :param months_name_list: list name of month
    :param new_month_table: list data
    :return:
    """
    year = now.year
    month = now.month
    directory_year(str(year))
    directory_month(months_name_list[month - 1], str(year))
    path = str(year) + '/' + months_name_list[month - 1]
    file_name = path + '/' + 'Status_' + months_name_list[month - 1] + '_' + str(year) + '.csv'
    start = ['Start time:', str(day) + '.' + months_name_list[month - 1] + '.' + str(year)]
    end = ['End time:', str(calendar.monthrange(year, month)[1]) + '.' + months_name_list[month - 1] + '.' + str(year)]
    table_csv = [start, end] + new_month_table
    write_csv(file_name, table_csv)


now = datetime.now(timezone.utc)

months_name_list = ['january', 'february', 'march', 'april',
                    'may', 'june', 'july', 'august', 'september',
                    'october', 'november', 'december']
day = now.day
year = now.year
month = now.month
str_month = months_name_list[month - 1]
str_year = str(year)
new_month_flag = False
if not os.path.exists(str_year):
    os.mkdir(str_year)
    os.mkdir(str_year + '/' + str_month)
    year -= 1
    month = 12
    new_month_flag = True
if not os.path.exists(str_year + '/' + str_month):
    os.mkdir(str_year + '/' + str_month)
    month -= 1
    new_month_flag = True

file_name = str_year + '/' + str_month + '/' + 'Status_' + str_month + '_' + str_year + '.csv'

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
    create_new_csv(now, months_name_list, new_month_table)
