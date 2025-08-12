# from sys import exit
from os import getcwd, listdir
from datetime import datetime, timedelta
from time import sleep
from pandas import read_excel, to_datetime, DataFrame, Series, ExcelWriter


"""
    x86 v1.2 修复bug：当员工打卡记录只有一条，且正好在判断白夜班时间范围之内，就会进入计算工时，返回-1，-1会导致引用下标报错
"""

def compute_work_hours(datetime_list, job_type, day_night=True):
    if day_night:
        time_area = DAY_TIME_AREA
    else:
        time_area = NIGHT_TIME_AREA
    datetime_list = datetime_list.tolist()
    if len(datetime_list) < 2:
        return (0.0, 0.0)

    daka = {'上班打卡': [], '工作时间1': [], '午休打卡': [], '休息时间1': [], '午休结束打卡': [],
            '工作时间2': [], '晚休打卡': [], '休息时间2': [], '晚休结束打卡': [],
            '工作时间3': [], '下班打卡': [], '超时打卡': []}

    work_hours = {'工作时间1': [], '工作时间2': [], '工作时间3': [], '超时': [], 'total': 0}
    # print('计算工时')
    compute_list = []
    for i in datetime_list:
        if time_area['上班打卡'] + timedelta(hours=-1) <= i < time_area['上班打卡']:
            daka['上班打卡'].append(i)
        elif time_area['上班打卡'] <= i < time_area['午休打卡']:
            daka['工作时间1'].append(i)
        elif time_area['午休打卡'] <= i < time_area['午休打卡'] + timedelta(minutes=15):
            daka['午休打卡'].append(i)
        elif time_area['午休打卡'] + timedelta(minutes=15) <= i < time_area['午休结束打卡'] + timedelta(minutes=-15):
            daka['休息时间1'].append(i)
        elif time_area['午休结束打卡'] + timedelta(minutes=-15) <= i < time_area['午休结束打卡']:
            daka['午休结束打卡'].append(i)
        elif time_area['午休结束打卡'] <= i < time_area['晚休打卡']:
            daka['工作时间2'].append(i)
        elif time_area['晚休打卡'] <= i < time_area['晚休打卡'] + timedelta(minutes=15):
            daka['晚休打卡'].append(i)
        elif time_area['晚休打卡'] + timedelta(minutes=15) <= i < time_area['晚休结束打卡'] + timedelta(minutes=-15):
            daka['休息时间2'].append(i)
        elif time_area['晚休结束打卡'] + timedelta(minutes=-15) <= i < time_area['晚休结束打卡']:
            daka['晚休结束打卡'].append(i)
        elif time_area['晚休结束打卡'] <= i < time_area['下班打卡']:
            daka['工作时间3'].append(i)
        elif time_area['下班打卡'] <= i < time_area['下班打卡'] + timedelta(minutes=15):
            daka['下班打卡'].append(i)
        elif time_area['下班打卡'] + timedelta(minutes=15) <= i < time_area['超时截止']:
            daka['超时打卡'].append(i)
        else:
            continue
        compute_list.append(i)

    for i in range(len(compute_list) - 1):
        work_hours['total'] += (compute_list[i + 1] - compute_list[i]).seconds / 3600

    if daka['上班打卡']:
        work_hours['total'] -= (time_area['上班打卡'] - min(daka['上班打卡'])).seconds / 3600

    if daka['午休打卡'] and daka['午休结束打卡']:
        work_hours['total'] -= 1.0
    elif daka['休息时间1'] and daka['午休结束打卡']:
        work_hours['total'] -= (3600 - (min(daka['休息时间1']) - time_area['午休打卡']).seconds) / 3600
    else:
        work_hours['total'] -= 1.0

    if job_type == '制造类':
        if daka['晚休打卡'] and daka['晚休结束打卡']:
            work_hours['total'] -= 1.5
        elif daka['休息时间2'] and daka['晚休结束打卡']:
            work_hours['total'] -= (5400 - (min(daka['休息时间2']) - time_area['晚休打卡']).seconds) / 3600
        else:
            work_hours['total'] -= 1.5

    # print(daka)
    # print(work_hours)
    if work_hours['total'] - int(work_hours['total']) >= 0.5:
        optimize_work_hours = int(work_hours['total']) + 0.5
    else:
        optimize_work_hours = round(work_hours['total'])
    # print(work_hours, float("{:.2f}".format(work_hours['total'])), round(optimize_work_hours, 1))
    return (float("{:.2f}".format(work_hours['total'])), round(optimize_work_hours, 1))


if __name__ == '__main__':

    origin_dir = getcwd()
    employee_file_path = origin_dir + '\\a.xls'
    while True:
        input_value = input('\n\nx86 版本1.2\n将\'员工资料.xls\'、\'打卡记录xxxx-xx-xx.xls\'的表格和程序放在同一个文件夹\n请输入日期（例如 20250723）（输入 \'q\' 退出）：')
        try:
            if input_value:
                if input_value == 'q':
                    break
                target_time = datetime.strptime(input_value, '%Y%m%d')
            else:
                try:
                    file_list = []
                    for i in listdir(getcwd()):
                        if i.startswith('打卡记录2025-') and i.endswith('.xls'):
                            file_list.append(int(i.split('打卡记录')[1].split('.xls')[0].replace('-', '')))
                    target_time = datetime.strptime(str(max(file_list)), '%Y%m%d')
                except:
                    print('error，未找到打卡记录文件。')
                    continue
#                     sleep(5)
#                     exit()
            daka_file_path = origin_dir + '\\a{}.xls'.format(target_time.strftime('%Y-%m-%d'))
            BASE_DATETIME = target_time
            print(target_time.date())

            DAY_TIME_AREA = {'上班打卡': BASE_DATETIME + timedelta(hours=8),
                             '午休打卡': BASE_DATETIME + timedelta(hours=12),
                             '午休结束打卡': BASE_DATETIME + timedelta(hours=13),
                             '晚休打卡': BASE_DATETIME + timedelta(hours=17),
                             '晚休结束打卡': BASE_DATETIME + timedelta(hours=18) + timedelta(minutes=30),
                             '下班打卡': BASE_DATETIME + timedelta(hours=20),
                             '超时截止': BASE_DATETIME + timedelta(days=1) + timedelta(hours=5)}
            NIGHT_TIME_AREA = {'上班打卡': BASE_DATETIME + timedelta(hours=20),
                               '午休打卡': BASE_DATETIME + timedelta(hours=24),
                               '午休结束打卡': BASE_DATETIME + timedelta(days=1) + timedelta(hours=1),
                               '晚休打卡': BASE_DATETIME + timedelta(days=1) + timedelta(hours=5),
                               '晚休结束打卡': BASE_DATETIME + timedelta(days=1) + timedelta(hours=6) + timedelta(
                                   minutes=30),
                               '下班打卡': BASE_DATETIME + timedelta(days=1) + timedelta(hours=8),
                               '超时截止': BASE_DATETIME + timedelta(days=1) + timedelta(hours=17)}
            print(BASE_DATETIME)
            print(DAY_TIME_AREA)
            print(NIGHT_TIME_AREA)
            print(employee_file_path,daka_file_path)

            employee_file = read_excel(employee_file_path,
                                          names=['ccid', 'name', 'department', 'job_type', 'job', 'child_department',
                                                 'active'])
            daka_file = read_excel(daka_file_path, sheet_name='Sheet1',
                                      names=['date', 'ccid', 'name', 'department', 'daka_type', 'datetime',
                                             'device_dedescription', 'device_uuid'])
            daka_file.drop([0, 1], inplace=True)
            daka_file['datetime'] = to_datetime(daka_file['datetime'], errors='coerce')

            employee_file.index = range(2, len(employee_file) + 2)
            daka_file.index = range(4, len(daka_file) + 4)
            daka_file.sort_values(by='datetime', inplace=True)
            new_file = DataFrame(
                columns=['ccid', 'name', 'department', 'job_type', 'job', 'child_department', 'date', 'work_type',
                         'actual_work_hours', 'work_hours', 'state', 'items']).astype(
                {'ccid': 'int', 'name': 'string', 'department': 'string', 'job_type': 'string', 'job': 'string',
                 'child_department': 'string', 'date': 'string',
                 'work_type': 'string', 'actual_work_hours': 'float', 'work_hours': 'float', 'state': 'string',
                 'items': 'string'})

            grouped = daka_file.groupby('ccid')

            work_day_datetime1 = BASE_DATETIME + timedelta(hours=11)
            work_day_datetime2 = BASE_DATETIME + timedelta(hours=18)
            work_night_datetime1 = BASE_DATETIME + timedelta(hours=23)
            work_night_datetime2 = BASE_DATETIME + timedelta(days=1) + timedelta(hours=6)

            for i in grouped.groups:
                # print(i, '\n', grouped.get_group(i))
                print(i)
                employee = employee_file[employee_file['ccid'] == grouped.get_group(i).iloc[0]['ccid']].to_dict(
                    orient="records")
                new_row_date = [grouped.get_group(i).iloc[0]['ccid'], grouped.get_group(i).iloc[0]['name'],
                                grouped.get_group(i).iloc[0]['department'], '', '', '', '', '', 0.0, 0.0, '', '']
                new_row = Series(new_row_date, index=new_file.columns)
                if employee:
                    employee = employee[0]
                    new_row['job_type'] = employee['job_type']
                    new_row['job'] = employee['job']
                    new_row['child_department'] = employee['child_department']
                else:
                    new_row['state'] = '异常，员工资料不存在考勤编号'
                    new_file = new_file.append(new_row, ignore_index=True)
                    continue
                for index, row in grouped.get_group(i).iterrows():
                    row = row.to_dict()
                    #                 print(index,'\n',row)
                    if work_day_datetime1 < row['datetime'] <= work_day_datetime2:
                        new_row['date'] = row['date']
                        new_row['work_type'] = 'day'
                        result = compute_work_hours(grouped.get_group(i)['datetime'], job_type=employee['job_type'])
                        new_row['actual_work_hours'] = result[0]
                        new_row['work_hours'] = result[1]
                        break
                    elif work_night_datetime1 < row['datetime'] <= work_night_datetime2:
                        new_row['date'] = row['date']
                        new_row['work_type'] = 'night'
                        result = compute_work_hours(grouped.get_group(i)['datetime'], job_type=employee['job_type'],
                                                    day_night=False)
                        new_row['actual_work_hours'] = result[0]
                        new_row['work_hours'] = result[1]
                        break
                if new_row['work_hours'] < 8.0 or new_row['work_hours'] > 9.5:
                    if new_row['work_hours'] > 9.5:
                        new_row['state'] = '超时'
                    else:
                        new_row['state'] = '异常'
                    items = []
                    for index, row in grouped.get_group(i).iterrows():
                        row = row.to_dict()
                        items.append('{},{},{},{}'.format(row['datetime'], row['daka_type'], row['device_dedescription'],
                                                          row['device_uuid']))
                    new_row['items'] = '\r\n'.join(items)
                new_row = new_row.replace('day', '白班')
                new_row = new_row.replace('night', '夜班')
                new_file = new_file.append(new_row, ignore_index=True)
            # print(new_file)
            new_file.fillna('')
	  
            writer = ExcelWriter('output_{}.xls'.format(BASE_DATETIME.date()), engine='xlsxwriter')
            new_file.to_excel(writer, sheet_name='Sheet1', index=False,
                              header=['考勤编号', '姓名', '部门', '类别', '职务', '子部门', '考勤日期', '班别', '实际工时',
                                      '工时', '状态', '打卡记录'])
            # 获取工作簿和工作表
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            # 添加单元格格式
            text_wrap_format = workbook.add_format({'text_wrap': True, 'align': 'right', 'valign': 'vcenter'})
            # 设置列宽和应用文本换行格式
            worksheet.set_column('A:F', 10, text_wrap_format)
            worksheet.set_column('G:G', 20, text_wrap_format)
            worksheet.set_column('H:K', 10, text_wrap_format)
            worksheet.set_column('L:L', 50, text_wrap_format)
            # 保存文件
            writer.save()
            print('\n-------完成{}-------'.format('output_{}.xls'.format(BASE_DATETIME.date())))

        except Exception as e:
            print()
            print(e)
            print('-------error-------')

#     print('-------5秒后结束-------')
#     sleep(5)
