#!/usr/bin/python3

import os
import argparse
import configparser
from datetime import datetime, timedelta
import requests
import ast
from sys import exit

class Clk:
  def __init__(self):
    #region envvars
    if "CLICKUP_PK" in os.environ:
      self.pk = os.environ["CLICKUP_PK"]
    else:
      print('CLICKUP_PK not set! please create a key for clickup at')
      print('https://clickup.com/api/developer-portal/authentication#personal-token')
      print('and set environment variable CLICKUP_PK to that value')
      exit()

    if "CLICKUP_TEAM_ID" in os.environ:
      self.team_id = os.environ["CLICKUP_TEAM_ID"]
    else:
      print('CLICKUP_TEAM_ID not set!')
      print('Your team id is the number after the base website domain')
      print('https://app.clickup.com/YOUR_ID_HERE')
      print('please set environment variable CLICKUP_TEAM_ID to that number.')
      exit()
    #endregion

    self.config_file_folder = os.path.expanduser('~') + '/.clk'
    self.config_file_path = self.config_file_folder + '/config'
    if (os.path.isdir(self.config_file_folder)):
      pass
    else:
      os.makedirs(self.config_file_folder)
    if (os.path.isfile(self.config_file_path)):
      self.read_config()
      self.first_run = False
    else:
      self.config = configparser.RawConfigParser()
      self.first_run = True
    if ("shortnames" not in self.config.sections()):
      self.config.add_section("shortnames")
      self.write_config()

  def read_config(self):
    self.config = configparser.RawConfigParser()
    self.config.optionxform = str
    self.config.read(self.config_file_path)

  def write_config(self):
    cfgfile = open(self.config_file_path,'w')
    self.config.write(cfgfile, space_around_delimiters=False)
    cfgfile.close()


  def open_config(self):
    print(self.config_file_path)
    cfgfile = open(self.config_file_path,'r')
    content = cfgfile.read()
    print(content)

  def is_integer(self, n):
      try:
          int(n)
          return True
      except ValueError:
          return False

  def guess(self):
    print('guess')
    print(self.config_file_path)

  def get_task_id_and_name(self, custom_id):
    custom_id = custom_id.upper()
    url = "https://api.clickup.com/api/v2/task/" + custom_id + "?custom_task_ids=true&team_id=" + self.team_id
    headers = {
      "Content-Type": "application/json",
      "Authorization": self.pk
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      return None, None
    json = response.json()
    return json["id"], json["name"]

  def create_entry(self, task_id, start_datetime, finish_datetime):
    url = "https://api.clickup.com/api/v2/team/" + self.team_id + "/time_entries"
    headers = {
      "Content-Type": "application/json",
      "Authorization": self.pk
    }
    timestamp_start = int(datetime.timestamp(start_datetime)) * 1000
    timestamp_finish = int(datetime.timestamp(finish_datetime)) * 1000
    payload = {
      "start": timestamp_start,
      "stop": timestamp_finish,
      "tid": task_id
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
      print(f'Error: {response.status_code}')
      print(response)
      return False
    return True
    

  def get_latest_entry(self):
    url = "https://api.clickup.com/api/v2/team/" + self.team_id + "/time_entries"
    headers = {
      "Content-Type": "application/json",
      "Authorization": self.pk
    }
    response = requests.get(url, headers=headers)
    json = response.json()
    entries = json["data"]
    terse_entries = []
    for e in entries:
      entry = {}
      entry["task"] = e["task"]
      entry["start"] = e["start"]
      entry["end"] = e["end"]
      terse_entries.append(entry)
    terse_entries = sorted(terse_entries, key=lambda x : x['start'], reverse=True)
    return terse_entries[0]

  def get_entries_since(self, start_epoch_with_milliseconds_as_string):
    url = "https://api.clickup.com/api/v2/team/" + self.team_id + "/time_entries"
    query = {
       "start_date": start_epoch_with_milliseconds_as_string
    }
    headers = {
      "Content-Type": "application/json",
      "Authorization": self.pk
    }
    response = requests.get(url, headers=headers, params=query)
    json = response.json()
    entries = json["data"]
    terse_entries = []
    for e in entries:
      entry = {}
      entry["task"] = e["task"]
      entry["start"] = e["start"]
      entry["end"] = e["end"]
      terse_entries.append(entry)
    terse_entries = sorted(terse_entries, key=lambda x : x['start'])
    return terse_entries

  def get_entries_in_datetime_range(self, start_date, end_date):
    end_epoch = int(datetime.timestamp(end_date))
    start_epoch = int(datetime.timestamp(start_date))
    clickup_end = f'{end_epoch}000'
    clickup_start = f'{start_epoch}000'
    return self.get_entries_in_range(clickup_start, clickup_end)

  def get_entries_in_range(self, start_epoch_with_milliseconds_as_string, end_epoch_with_milliseconds_as_string):
    url = "https://api.clickup.com/api/v2/team/" + self.team_id + "/time_entries"
    query = {
       "start_date": start_epoch_with_milliseconds_as_string,
       "end_date": end_epoch_with_milliseconds_as_string
    }
    headers = {
      "Content-Type": "application/json",
      "Authorization": self.pk
    }
    response = requests.get(url, headers=headers, params=query)
    json = response.json()
    entries = json["data"]
    terse_entries = []
    for e in entries:
      entry = {}
      entry["task"] = e["task"]
      entry["start"] = e["start"]
      entry["end"] = e["end"]
      terse_entries.append(entry)
    terse_entries = sorted(terse_entries, key=lambda x : x['start'])
    return terse_entries

  def recent(self):
    start_date = datetime.today() - timedelta(30)
    start_as_epoch = int(datetime.timestamp(start_date))
    epoch_for_clickup = f'{start_as_epoch}000'
    entries = self.get_entries_since(epoch_for_clickup)
    for doc in entries:
      start = doc["start"][:-3]
      stop = doc["end"][:-3]
      start_format = '%a %m-%d %H:%M'
      stop_format = '%H:%M'
      formatted_start = datetime.fromtimestamp(int(start)).strftime(start_format)
      formatted_stop = datetime.fromtimestamp(int(stop)).strftime(stop_format)
      task = doc["task"]
      if "custom_id" in task:
        custom_id = task["custom_id"]
      else:
        custom_id = ''
      print(f'{formatted_start} to {formatted_stop} {custom_id} {task["name"]}')
  
  def get_start_and_end_of_week(self, datetime_in_week):
    day_of_week = datetime_in_week.weekday()
    if (day_of_week == 6):
      first_day_of_week = datetime_in_week.date()
    else:
      first_day_of_week = datetime_in_week.date() - timedelta(day_of_week + 1)
    last_day_of_week = first_day_of_week + timedelta(6)
    start_datetime = datetime(first_day_of_week.year, first_day_of_week.month, first_day_of_week.day)
    end_datetime = datetime(last_day_of_week.year, last_day_of_week.month, last_day_of_week.day, 23, 59, 59)
    result = {}
    result["start"] = start_datetime
    result["end"] = end_datetime
    return result
    #return start_datetime, end_datetime

  def bins(self, num_weeks=1):
    now = datetime.today()
    weeks = []
    for i in range(num_weeks - 1, -1, -1):
      week = self.get_start_and_end_of_week(now - timedelta(7 * i))
      week["entries"] = self.get_entries_in_datetime_range(week["start"], week["end"])
      weeks.append(week)
    for week in weeks:
      self.print_week_summary(week)
    
  def print_week_summary(self, week):
    # day index: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
    DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    ZERO = timedelta(0)

    buckets = {}   # name -> {day_index: timedelta, ...}
    grand_total = ZERO
    has_sunday = False
    has_saturday = False

    for doc in week["entries"]:
      string_start = doc["start"][:-3]
      string_stop = doc["end"][:-3]
      start = datetime.fromtimestamp(int(string_start))
      stop = datetime.fromtimestamp(int(string_stop))
      task = doc["task"]
      name = task["name"]
      grand_total += stop - start
      if name not in buckets:
        buckets[name] = {}
      midnight = datetime(start.year, start.month, start.day) + timedelta(days=1)
      slices = [(start, min(stop, midnight)), (midnight, stop)] if stop > midnight else [(start, stop)]
      for slice_start, slice_end in slices:
        py_dow = slice_start.weekday()
        day_idx = (py_dow + 1) % 7
        if day_idx == 0:
          has_sunday = True
        if day_idx == 6:
          has_saturday = True
        buckets[name][day_idx] = buckets[name].get(day_idx, ZERO) + (slice_end - slice_start)

    # build ordered list of day columns to show
    core_days = [1, 2, 3, 4, 5]  # Mon–Fri always shown
    col_days = ([0] if has_sunday else []) + core_days + ([6] if has_saturday else [])

    NAME_W = 26
    COL_W = 6   # e.g. " 3.25"

    def fmt_h(td):
      h = td.total_seconds() / 3600
      return f'{h:.2f}'.rjust(COL_W)

    def blank_col():
      return ' ' * COL_W

    # header
    week_label = f'Week of {datetime.date(week["start"])}'
    header_days = ''.join(DAY_NAMES[d].rjust(COL_W) for d in col_days) + ' Total'.rjust(COL_W + 2)
    border_w = NAME_W + len(header_days)
    border = '─' * border_w

    print()
    print('  ' + week_label.ljust(NAME_W) + header_days)
    print('  ' + border)

    for name in sorted(buckets):
      row = name[:NAME_W - 1].ljust(NAME_W)
      name_total = ZERO
      for d in col_days:
        td = buckets[name].get(d, ZERO)
        name_total += td
        row += fmt_h(td) if td else blank_col()
      row += fmt_h(name_total).rjust(COL_W + 2)
      print('  ' + row)

    print('  ' + border)
    # totals row
    total_row = 'TOTAL'.ljust(NAME_W)
    for d in col_days:
      day_total = sum((buckets[n].get(d, ZERO) for n in buckets), ZERO)
      total_row += fmt_h(day_total) if day_total else blank_col()
    total_row += fmt_h(grand_total).rjust(COL_W + 2)
    print('  ' + total_row)
    print()

  def do_first_run(self):
    print('I see it is the first time running this.')
    print(' ')
    print('Retrieving recent clickup time entries to populate list of convenient customer short names.')
    print(' ')
    self.try_to_populate_short_names()

  def try_to_populate_short_names(self):
    start_date = datetime.today() - timedelta(30)
    start_as_epoch = int(datetime.timestamp(start_date))
    epoch_for_clickup = f'{start_as_epoch}000'
    entries = self.get_entries_since(epoch_for_clickup)
    customers = {}
    for doc in entries:
      task = doc["task"]
      id = task["id"]
      name = task["name"]
      if "custom_id" in task:
        custom_id = task["custom_id"]
      else:
        custom_id = ''
      custom_id = custom_id.lower()
      if id not in customers:
        customers[id] = [custom_id, name]
    writable_customers = {}
    for id in customers:
      custom_id = customers[id][0]
      name = customers[id][1]
      pieces_of_name = name.split(' ')
      if len(pieces_of_name) < 6:
        # we could make the short name the first piece
        short_name = (pieces_of_name[0]).lower()
      else:
        continue
      writable_customers[short_name] = [custom_id, id]
    for short_name in writable_customers:
      self.config.set("shortnames", short_name, writable_customers[short_name])
    self.write_config()
    print('use -show-config option to see shortnames available to -add command')

  def add(self, args):
    # Syntax 1
    # clk.py -add since last shortname
      # false false false

    # Syntax 2
    # clk.py -add 1300 1330 shortname
      # true true false

    # Syntax 3
    # clk.py -add 10 min cust-2977
      # true false false

    if len(args) == 2:
      combined = args[0]
      if len(combined) > 1 and combined[-1] in ['m', 'h'] and self.is_integer(combined[:-1]):
        args = [combined[:-1], combined[-1], args[1]]
      else:
        print('Invalid syntax')
        print('Please use')
        print('clk add since last SHORTNAME')
        print('clk add 1300 1330 SHORTNAME')
        print('clk add 10 min SHORTNAME')
        print('clk add 10m SHORTNAME')
        exit()
    elif len(args) != 3:
      print('Invalid syntax')
      exit()

    syntax_seen = 'invalid'

    if (self.is_integer(args[2])):
      print('3rd -add argument should always be the customer task id or shortname.')
      print('An integer was passed so we are exiting.')
      print(args[2])
      exit()

    if (args[0] == 'since' and args[1] == 'last'):
      syntax_seen = '1'
    elif (self.is_integer(args[0]) and self.is_integer(args[1])):
      arg0 = int(args[0])
      arg1 = int(args[1])
      syntax_seen = '2'
      if (arg0 < 0 or arg0 > 2359 or arg1 < 0 or arg1 > 2359):
        print('1st and 2nd -add arguments should be in the range from 0 to 2359 when specifying times.')
        exit()
    elif (self.is_integer(args[0]) and args[1] in ['min','hour','m','h']):
      syntax_seen = '3'
    else:
      print('Invalid syntax')
      print('Please use')
      print('clk add since last SHORTNAME')
      print('clk add 1300 1330 SHORTNAME')
      print('clk add 10 min SHORTNAME')
      print('clk add 10m SHORTNAME')
      exit()

    passed_id = args[2]

    found_short_name = ''
    found_custom_id = ''
    found_id = ''
    short_names = self.config.items('shortnames')
    for key, string_value in short_names:
      value = ast.literal_eval(string_value)
      if (passed_id == key or passed_id == value[0] or passed_id == value[1]):
        found_short_name = key
        found_custom_id = value[0]
        found_id = value[1]
        break
    if found_short_name == '':
      print(f'{passed_id} not found in short name cache')
      task_id, task_name = self.get_task_id_and_name(passed_id)
      if (task_id is None):
        print(f'{passed_id} not found in Clickup')
        exit()
      else:
        print(f'Found in Clickup: {task_id} {task_name}')
        pieces_of_name = task_name.split(' ')
        short_name = (pieces_of_name[0]).lower()
        custom_id = passed_id.lower()
        print(f'Writing shortname record to config: {short_name}=["{custom_id}", "{task_id}"]')
        self.config.set("shortnames", short_name, [custom_id, task_id])
        self.write_config()
        found_short_name = short_name
        found_id = task_id
        found_custom_id = custom_id

    now = datetime.now()

    if (syntax_seen == '1'):
      # find most recent entry and create an entry that starts when that one stops and goes until {now}
      latest = self.get_latest_entry()
      stop_format = '%m-%d %H:%M'
      stop = latest["end"][:-3]
      entry_start = datetime.fromtimestamp(int(stop)) #.strftime(stop_format)
      entry_finish = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)

    elif (syntax_seen == '2'):
      start = int(args[0])
      finish = int(args[1])
      start_hour = start // 100 * 100
      start_minute = start - start_hour
      start_hour /= 100
      start_hour = int(start_hour)
      finish_hour = finish // 100 * 100
      finish_minute = finish - finish_hour
      finish_hour /= 100
      finish_hour = int(finish_hour)
      year = now.year
      month = now.month
      day = now.day
      entry_start = datetime(year, month, day, start_hour, start_minute)
      entry_finish = datetime(year, month, day, finish_hour, finish_minute)

    elif (syntax_seen == '3'):
      quantity = int(args[0])
      unit = args[1]
      if (unit in ['min','m']):
        negative_quantity = quantity * -1
        cleaned_now = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
        entry_start = cleaned_now + timedelta(minutes=negative_quantity)
        entry_finish = cleaned_now

    else:
      print('unsupported syntax')
      exit()
    
    was_created = self.create_entry(found_id, entry_start, entry_finish)
    if (was_created):
      print(f'Created entry from {entry_start} to {entry_finish} for {found_short_name} {found_custom_id}')
    else:
      print(f'Unsuccessful trying to create entry from {entry_start} to {entry_finish} for {found_short_name} {found_custom_id}')


  def parse_args_branch_execution(self):
    parser = argparse.ArgumentParser("./clk.py")
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help="add new time entry")
    add_parser.add_argument('args', nargs='+', metavar='ARG')

    subparsers.add_parser('recent', help="show entries from past 30 days")
    subparsers.add_parser('show-config', help="show config file of customer shortnames")
    bins_parser = subparsers.add_parser('bins', help="show summary breakdown")
    bins_parser.add_argument('weeks', nargs='?', type=int, default=1, metavar='WEEKS', help="number of weeks to show (default: 1)")

    args = parser.parse_args()

    if args.command == 'add':
      self.add(args.args)
    elif args.command == 'show-config':
      self.open_config()
    elif args.command == 'recent':
      self.recent()
    elif args.command == 'bins':
      self.bins(args.weeks)
    else:
      parser.print_help()

clk = Clk()
if (clk.first_run):
  clk.do_first_run()
else:
  clk.parse_args_branch_execution()