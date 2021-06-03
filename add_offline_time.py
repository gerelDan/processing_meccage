import json
import time
import requests as req
from datetime import datetime, timezone, timedelta
import calendar
import os.path
from tokens import token_api


def directory_year(year_now: str):
    """
    this function check availability folder with name year and create this
    if this folder not found
    :param year_now: str
    :return:
    """
    if not os.path.exists(year_now):
        os.mkdir(year_now)


def directory_month(month_now: str, year_now: str):
    """
    this function check availability folder with name year\\month and create this
    if this folder not found
    :param month_now: str
    :param year_now: str
    :return:
    """
    if not os.path.exists(year_now + '/' + month_now):
        os.mkdir(year_now + '/' + month_now)


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
    if len(resp_json) == 4:
        return resp_json
    else:
        print('Station not found')
        return 'Station not found'


def get_time_offline(now, data_list: list, new_month_flag: bool, new_month_table: list, station_ids: dict):
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
            now = datetime.strptime((str(now)[:10] + 'T' + str(now)[11:19]), '%Y-%m-%dT%H:%M:%S')
            try:
                resp_json = get_json_text(station_ids[station_id])
            except:
                print('Station not found')
                line[-1] = 'Station not found'
                continue
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

def time_off_time(data: list, stations: dict):
    """
    this function calculate time offline for all station from last month
    :param stations: dict station id
    :param data: list all detected errors from month
    :return: dict
    """
    time_off =dict()
    for station in stations:
        time_offline_ststion = timedelta()
        for line in data:
            if station.lower() == line[4]:
                timesy = line[-1].split(', ')
                if len(timesy) > 1:
                    day = timesy[0]
                    timing = timesy[1].split(':')
                    tdt = timedelta(
                        days=int(day.split(' ')[0]),
                        hours=int(timing[0]),
                        minutes=int(timing[1]),
                        seconds=int(timing[2])
                    )

                elif len(timesy) == 1 and timesy[0] != '':
                    timing = timesy[0].split(':')
                    tdt = timedelta(
                        days=int(day.split(' ')[0]),
                        hours=int(timing[0]),
                        minutes=int(timing[1]),
                        seconds=int(timing[2])
                    )
                time_offline_ststion += tdt
        time_off[station] = str(time_offline_ststion)
    return time_off

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

str_month = months_name_list[month - 1]
str_year = str(year)
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
stations.pop('Charging Station ID')
new_month_table = []

data, new_month_table = get_time_offline(now, data, new_month_flag, new_month_table, stations)

table_csv = header + data

write_csv(file_name, table_csv)

if new_month_flag:
    create_new_csv(now, months_name_list, new_month_table)
    time_off = time_off_time(data, stations)
    file_name_analyze = str_year + '/' + str_month + '/' + 'analyze_' + str_month + '_' + str_year + '.csv'
    table = open(file_name_analyze, 'w')
    table.write('Station;time_offline' + '\n')
    for station in time_off:
        table.write(station +';' + time_off[station] + '\n')
    table.close()