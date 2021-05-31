#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone

import win32com.client

import os.path

import calendar


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
    return elem


def read_csv(file_name: str):
    """
    give this function a file name and it will read it
    :param file_name: is a name file
    :return: the entire file is divided into rows a list of rows is obtained
    and each row is divided into columns separated by ';'
    """
    list_data = []
    csv_file = open(file_name, 'r')
    for line in csv_file:
        list_data.append(line[:-1].split(';')[:-1])
    csv_file.close()
    return list_data


def write_csv(file: str, list_of_processed_messages: list):
    """
    give this function a file name and a list and function write this list in file
    :param file: str
    :param list_of_processed_messages: list
    :return:
    """
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
    inbox = outlook.GetDefaultFolder(6)
    return inbox.Items


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


today = datetime.now()
now_utc = datetime.now(timezone.utc)

months = ['january', 'february', 'march', 'april',
          'may', 'june', 'july', 'august', 'september',
          'october', 'november', 'december']

day = now_utc.day
year = str(now_utc.year)
month = now_utc.month
month_str = months[month - 1]

directory_year(str(year))
directory_month(month_str, str(year))

file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + month_str + '_' + year + '.csv'

if not os.path.exists(file_name):
    data = open(file_name, 'w')
    start = 'Start time:;' + str(day) + '.' + month_str + '.' + str(year)
    end = 'End time:;' + str(calendar.monthrange(year, month)[1]) + '.' + months[month - 1] + '.' + str(year)
    data.write(start + '\n')
    data.write(end + '\n')
    data.write('event_timestamp;notification_timestamp;notification_profile;charging_station_name;'
               'charging_station_id;event_type;error_code;notification_message;online_time' + '\n')
    data.close()
    df = read_csv(file_name)

else:
    df = read_csv(file_name)

message_report = []

day_ago = today - timedelta(hours=25)

messages = connect_box()

messages.Sort("[CreationTime]", True)

message = messages.Find(
    "[SenderName] = 'AWS Notifications' And ([CreationTime] > day_ago)"
)
while True:
    try:
        body_content = message.Body
        try:
            content = pars_mail(body_content)
            rows = ';'.join(content)
            if content[:-1] not in df:
                message_report.append(rows)
            message.Unread = False

        except Exception as err:  # доработать логи
            log = open('logs.txt', 'a')
            log.write(str(message.CreationTime)[0:19] + ' ' + str(message.SenderName) + ' '
                      + str(message.Subject) + str(err) + '\n')
            log.close()
            pass

    except Exception:
        break
    message = messages.FindNext()

message_report.sort()
write_csv(file_name, message_report)
