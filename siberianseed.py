#!/usr/bin/python

import sys
import os
import json
import multiprocessing as mp
import subprocess

DIR_APPS = 'apps'
DIR_APP_BIN = 'bin'
DIR_APP_SRC = 'src'
DIR_APP_SHARE = 'share'
PATH_DEFINE = 'define.json'
PATH_MAP = 'map.json'
PATH_UTILS = 'utils.json'

seed = sys.argv[1]
route = sys.argv[2] if len(sys.argv) > 2 else None
param_one = sys.argv[3] if len(sys.argv) > 3 else None
define = {}
taskmap = {}
apps = []
apps_tasks = {}
utils = {}

if not os.path.exists(DIR_APPS):
  os.makedirs(DIR_APPS)

if os.path.exists(PATH_DEFINE):
  handle = open(PATH_DEFINE)
  define_str = handle.read()
  define = json.loads(define_str)
  handle.close()

if os.path.exists(PATH_MAP):
  handle = open(PATH_MAP)
  taskmap_str = handle.read()
  taskmap = json.loads(taskmap_str)
  handle.close()

if os.path.exists(PATH_UTILS):
  handle = open(PATH_UTILS)
  utils_str = handle.read()
  utils = json.loads(utils_str)
  handle.close()

def list_app_tasks(app):
  dir_bin = '/'.join([DIR_APPS, app, DIR_APP_BIN])
  if not os.path.exists(dir_bin):
    return []
  return map(
    lambda s: s[0:-3], 
    filter(
      None, 
      [
        taskfile 
        if taskfile.endswith('.sh') 
        else None 
        for taskfile in os.listdir(dir_bin)
      ]
    )
  )

def print_if(condition, str):
  if condition:
    print(str)

def run(app, tasks, prefix):
  print('Running [' + app + ']: ' + json.dumps(tasks))

  for task in tasks:
    shell_src = prefix + open('/'.join([DIR_APPS, app, DIR_APP_BIN, task + '.sh'])).readlines()
    child = subprocess.Popen('\n'.join(shell_src), shell=True)
    child.communicate()
    if child.returncode is not 0:
      print_if(print_errors, ' ERROR [%s] %s: returned code %s' % (app, task, str(child.returncode)))

def execute(apptasks):
  jobs = []
  for app, tasks in apptasks.items():
    prefix = []
    prefix.append('%s="%s"' % ('root', os.getcwd()))
    for _app in apps:
      prefix.append('app_%s="%s/%s/%s/%s"' % (_app, os.getcwd(), DIR_APPS, _app, DIR_APP_SHARE))
    for variable, value in define.get(app, {}).items():
      prefix.append('%s="%s"' % (variable, value))
    prefix.append('cd %s/%s/%s/%s' % (os.getcwd(), DIR_APPS, app, DIR_APP_SHARE))
    jobs.append(mp.Process(
      target=run,
      args=(app, tasks, prefix)
    ))
  for j in jobs:
    j.start()
  for j in jobs:
    j.join()

print_errors = True
print_apps = True
print_tasks = True

if not route:
  pass
elif route == 'app':
  print_tasks = False
  if param_one:
    print_apps = False
elif route == 'run':
  print_apps = False
  if param_one:
    print_tasks = False
elif route == 'util':
  print_apps = False
  print_tasks = False
else:
  print_if(print_errors, ' ERROR [INPUT] Route unknown: ' + route)
  exit()

print_if(True, '')
print_if(True, ' # %s Management Console # ' % seed)
print_if(True, '')

print_if(print_apps, " @%s Apps List " % seed)
print_if(print_apps, '----------------')

apps = filter(None, [dir if os.path.isdir(DIR_APPS + '/' + dir) else None for dir in os.listdir(DIR_APPS)])
for app in apps:
  print_if(print_apps, app)
  apps_tasks[app] = list_app_tasks(app)
  for task in apps_tasks[app]:
    print_if(print_apps, ' > ' + task)
print_if(print_apps, '--------')
print_if(print_apps, '')

print_if(print_tasks, " @%s Task Map " % seed)
print_if(print_tasks, '---------------')

for root_task, subtasks in taskmap.items():
  errors = []
  for subtask in subtasks:
    if not isinstance(subtask, dict):
      if not str(subtask) in taskmap.keys():
        errors.append(' ERROR [TASKMAP] Task not found: ' + subtask)
    elif isinstance(subtask, dict):
      for app, app_tasks in subtask.items():
        tasks_not_found = filter(
          None, 
          [task if task not in apps_tasks.get(app, []) else None for task in app_tasks]
        )
        if len(tasks_not_found) > 0:
          errors.append(' ERROR [' + app + '] Tasks not found: ' + ', '.join(tasks_not_found))

  if len(errors) > 0:
    print_if(print_tasks, '' + root_task + ' - NOT OK!')
    for error in errors:
      print_if(print_errors, error)
  else:
    print_if(print_tasks, root_task + ' - OK')
print_if(print_tasks, '--------')
print_if(print_tasks, '')

if route == 'app' and param_one:
  app = param_one
  if os.path.exists(DIR_APPS + '/' + app):
    print_if(print_errors, ' ERROR ['+app+'] Destination exists.')
    exit()
  os.makedirs('/'.join([DIR_APPS, app, DIR_APP_BIN]))
  os.makedirs('/'.join([DIR_APPS, app, DIR_APP_SRC]))
  os.makedirs('/'.join([DIR_APPS, app, DIR_APP_SHARE]))
  print(' > App created: ' + param_one)
  print('')

if route == 'run' and param_one:
  task = param_one
  subtasks = taskmap.get(task, [])
  for sub in subtasks:
    if not isinstance(sub, dict):
      if str(sub) in taskmap.keys():
        subtasks = taskmap.get(sub)
        for _sub in subtasks:
          execute(_sub)
    elif isinstance(sub, dict):
      execute(sub)

if route == 'util' and param_one:
  util_src = utils.get(param_one, '')
  child = subprocess.Popen(util_src, shell=True)
  child.communicate()
  if child.returncode is not 0:
    print_if(print_errors, ' ERROR [UTIL] %s: returned code %s' % (param_one, str(child.returncode)))