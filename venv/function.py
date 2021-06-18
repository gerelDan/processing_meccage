import win32com.client
from datetime import datetime, timedelta, timezone
import os.path
import calendar
import time
import json
import requests as req
import calendar
from tokens import token_api


def pars_mail(body_mail):
    """
    This function search columns and row in message of report
    :param body_mail: body mail
    :return: list
    """

    pars_body = body_mail.split('\r\n')
    elem = []
    flag = False
    for row in pars_body[1:14]:
        if row == '':
            continue
        elif ': ' in row:
            line_mail = row.split(': ')
            elem.append(line_mail[1])
        elif row.endswith(':'):
            flag = True
        elif flag:
            elem.append(row)
            flag = False
        else:
            elem.append(row)

    for el in range(2, len(elem)):
        elem[el] = elem[el].lower()
        elem[el] = elem[el].replace(' ', '_')
    elem.append('')
    if len(elem) < 9:
        elem = pars_mail(body_mail)
    return elem


def read_csv(file_name: str):
    """
    give this function a file name and it will read it
    :param file_name: is a name file
    :return: the entire file is divided into rows a list of rows is obtained
    and each row is divided into columns separated by ','
    """
    list_data = []
    csv_file = open(file_name, 'r')
    for line in csv_file:
        list_data.append(line[:-1].split(',')[:-1])
    csv_file.close()
    head = list_data[:3]
    head = [','.join(head[0]), ','.join(head[1]), ','.join(head[2])]
    data = list_data[3:]
    return head, data


def write_csv(file: str, list_of_processed_messages: list):
    """
    give this function a file name and a list and function write this list in file
    :param file: str
    :param list_of_processed_messages: list
    :return:
    """
    try:
        table = open(file, 'a')
        for line_report in list_of_processed_messages:
            table.write(line_report + '\n')
        table.close()
    except Exception:
        time.sleep(10)
        table = open(file, 'a')
        for line_report in list_of_processed_messages:
            table.write(line_report + '\n')
        table.close()

def connect_box():
    """
    this function connect to your mailbox outlook folder inbox
    :return: all massage folder inbox
    """
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    if str(outlook.Folders(1)) == 'Archives':
        i = 2
    else:
        i = 1
    inbox = outlook.Folders(i)
    for j in range(1, 50):
        if 'AWS' in str(inbox.Folders(j)):
            AWS = inbox.Folders(j)
            break
    return AWS.Items


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
        
        
def write_csv_with_try(file: str, message_report: list):
    """
    this function write csv file and if this file is busy then function waiting 10 seconds
    :param file: str
    :param message_report: list
    :return:
    """
    try:
        table = open(file, 'w')
        for line_report in message_report:
            table.write(','.join(line_report) + '\n')
    except Exception:
        time.sleep(10)
        table = open(file, 'w')
        for line_report in message_report:
            table.write(','.join(line_report) + '\n')
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
#    print(resp_json)
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
    now_offline = set()
    for line in data_list:
        if line[-1] == '':
            station_id = line[4].upper()
            now_offline.add(station_id)
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
            times = statuses[connectors]['connectorStatus']['lastUpdated']
            for connector_num in range(len(statuses)):
                connector_statuses.append(statuses[connector_num]['connectorStatus']['status'])
                if statuses[connector_num]['connectorStatus']['status'] in ('OCCUPIED', 'AVAILABLE') and statuses[connector_num]['connectorStatus']['lastUpdated'] >= times:
                    connectors = connector_num

            last_update = datetime.strptime(
                statuses[connectors]['connectorStatus']['lastUpdated'][:19], '%Y-%m-%dT%H:%M:%S')

            if status == 'ONLINE' and (('AVAILABLE' in connector_statuses) or ('OCCUPIED' in connector_statuses)):
                times_off = str(last_update - event_time_stamp)
                times_off = times_off.replace(',', ' ')
                line[-1] = times_off
                now_offline.remove(station_id)
            elif new_month_flag:
                new_month_table.append(line)
                times_off = str(now - last_update)
                times_off = times_off.replace(',', ' ')
                line[-1] = times_off
    print(f'now offline : {now_offline}')
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
    day = now.day
    directory_year(str(year))
    directory_month(months_name_list[month - 1], str(year))
    path = str(year) + '/' + months_name_list[month - 1]
    file_name = path + '/' + 'Status_' + months_name_list[month - 1] + '_' + str(year) + '.csv'
    start = ['Start time:', str(day) + '.' + months_name_list[month - 1] + '.' + str(year)]
    end = ['End time:', str(calendar.monthrange(year, month)[1]) + '.' + months_name_list[month - 1] + '.' + str(year)]
    head = ['event_timestamp', 'notification_timestamp', 'notification_profile', 'charging_station_name',
                   'charging_station_id', 'event_type', 'error_code', 'notification_message', 'online_time']
    table_csv = [start, end, head] + new_month_table
    write_csv_with_try(file_name, table_csv)

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
                        hours=int(timing[0]),
                        minutes=int(timing[1]),
                        seconds=int(timing[2])
                    )
                time_offline_ststion += tdt
        time_off[station] = str(time_offline_ststion)
    return time_off