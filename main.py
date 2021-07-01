#!/usr/bin/env python3
import datetime
import os.path

import schedule

from function import *


def take_mails():
    now_utc = datetime.now(timezone.utc)
    months = ['january', 'february', 'march', 'april',
              'may', 'june', 'july', 'august', 'september',
              'october', 'november', 'december']

    day = now_utc.day
    year = now_utc.year
    year_str = str(now_utc.year)
    month = now_utc.month
    month_str = months[month - 1]

    directory_year(str(year))
    directory_month(month_str, str(year))

    file_name = str(year) + '/' + months[month - 1] + '/' + 'Status_' + month_str + '_' + year_str + '.csv'

    if not os.path.exists(file_name):
        data = open(file_name, 'w')
        start = 'Start time:,' + str(day) + '.' + month_str + '.' + str(year)
        end = 'End time:,' + str(calendar.monthrange(year, month)[1]) + '.' + months[month - 1] + '.' + str(year)
        data.write(start + '\n')
        data.write(end + '\n')
        data.write('event_timestamp,notification_timestamp,notification_profile,charging_station_name,'
                   'charging_station_id,event_type,error_code,notification_message,online_time' + '\n')
        data.close()
        df = read_csv(file_name)[1]

    else:
        df = read_csv(file_name)[1]

    message_report = []
    day_ago = now_utc + timedelta(hours=3)

    messages = connect_box()
    messages.Sort("[CreationTime]", True)
    for i in range(len(messages)):
        try:
            if messages[i].CreationTime < day_ago:
                break
        except Exception as err:
            print(err)
            log = open('logs.txt', 'a')
            log.write(str(now_utc) + ' ' + str(messages[i].SenderName) + ' '
                      + str(messages[i].Subject) + str(err) + '\n')
            log.close()
            continue
        print(messages[i].CreationTime, '>', day_ago, 'continue')
        try:
            body_content = messages[i].Body
            try:
                content = pars_mail(body_content)
                rows = ','.join(content)
                if content[:-1] not in df:
                    message_report.append(rows)
                messages[i].Unread = False

            except Exception as err:  # доработать логи
                log = open('logs.txt', 'a')
                log.write(str(messages[i].CreationTime)[0:19] + ' ' + str(messages[i].SenderName) + ' '
                          + str(messages[i].Subject) + str(err) + '\n')
                log.close()
                pass

        except Exception:
            break
    message_report.sort()
    to_csv = message_report
    write_csv(file_name, to_csv)


def add_offline_time():
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
        data = open(file_name, 'w')
        start = 'Start time:,' + str(day) + '.' + str_month + '.' + str(year)
        end = 'End time:,' + str(calendar.monthrange(year, month)[1]) + '.' + months_name_list[month - 1] + '.' + str(
            year)
        data.write(start + '\n')
        data.write(end + '\n')
        data.write('event_timestamp,notification_timestamp,notification_profile,charging_station_name,'
                   'charging_station_id,event_type,error_code,notification_message,online_time' + '\n')
        data.close()

    reports = open(file_name, 'r')
    for line in reports:
        table_csv.append(line[:-1].split(','))
    header = table_csv[:3]
    data = table_csv[3:]
    reports.close()

    s_id = open('Station_ID.csv', 'r')
    stations = {x[:-1].split(';')[0]: x[:-1].split(';')[1] for x in s_id}
    s_id.close()
    stations.pop('Charging Station ID')
    new_month_table = []
    data, new_month_table = get_time_offline(now, data, new_month_flag, new_month_table, stations)
    table_csv = header + data
    write_csv_with_try(file_name, table_csv)

    if new_month_flag:
        create_new_csv(now, months_name_list, new_month_table)
        time_off = time_off_time(data, stations)
        file_name_analyze = str_year + '/' + str_month + '/' + 'analyze_' + str_month + '_' + str_year + '.csv'
        table = open(file_name_analyze, 'w')
        table.write('Station,time_offline' + '\n')
        for station in time_off:
            table.write(station + ',' + time_off[station] + '\n')
        table.close()
    global start_program_timestamp
    now_work = datetime.utcnow()
    print('sum time work script:', now_work - start_program_timestamp)
    print('last time script worked:', now_work)


start_program_timestamp = datetime.utcnow()
take_mails()
add_offline_time()
schedule.every(10).minutes.do(take_mails)
schedule.every().hour.do(take_mails)
schedule.every(5).minutes.do(add_offline_time)
schedule.every().hour.do(add_offline_time)
while True:
    schedule.run_pending()
    time.sleep(1)
