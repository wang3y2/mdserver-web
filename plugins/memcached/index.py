# coding:utf-8

import sys
import io
import os
import time

sys.path.append(os.getcwd() + "/class/core")
import public

app_debug = False
if public.getOs() == 'darwin':
    app_debug = True


def getPluginName():
    return 'memcached'


def getPluginDir():
    return public.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return public.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getConf():
    path = getPluginDir() + "/init.d/memcached.tpl"
    return path


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    for i in range(len(args)):
        t = args[i].split(':')
        tmp[t[0]] = t[1]
    return tmp


def status():
    data = public.execShell(
        "ps -ef|grep " + getPluginName() + " |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def initDreplace():

    file_tpl = getConf()
    service_path = public.getServerDir()

    initD_path = getServerDir() + '/init.d'
    if not os.path.exists(initD_path):
        os.mkdir(initD_path)
    file_bin = initD_path + '/memcached'

    # if os.path.exists(file_bin):
    #     return file_bin

    content = public.readFile(file_tpl)
    content = content.replace('{$SERVER_PATH}', service_path)

    public.writeFile(file_bin, content)
    public.execShell('chmod +x ' + file_bin)
    return file_bin


def start():
    file = initDreplace()
    data = public.execShell(file + ' start')
    if data[1] == '':
        return 'ok'
    return 'fail'


def stop():
    file = initDreplace()
    data = public.execShell(file + ' stop')
    if data[1] == '':
        return 'ok'
    return 'fail'


def restart():
    file = initDreplace()
    data = public.execShell(file + ' reload')
    if data[1] == '':
        return 'ok'
    return 'fail'


def reload():
    file = initDreplace()
    data = public.execShell(file + ' reload')
    if data[1] == '':
        return 'ok'
    return 'fail'


def runInfo():
    # 获取memcached状态
    import telnetlib
    import re

    try:
        tn = telnetlib.Telnet('127.0.0.1', 11211)
        tn.write(b"stats\n")
        tn.write(b"quit\n")
        data = tn.read_all()
        if type(data) == bytes:
            data = data.decode('utf-8')
        data = data.replace('STAT', '').replace('END', '').split("\n")
        result = {}
        res = ['cmd_get', 'get_hits', 'get_misses', 'limit_maxbytes', 'curr_items', 'bytes',
               'evictions', 'limit_maxbytes', 'bytes_written', 'bytes_read', 'curr_connections']
        for d in data:
            if len(d) < 3:
                continue
            t = d.split()
            if not t[0] in res:
                continue
            result[t[0]] = int(t[1])
        result['hit'] = 1
        if result['get_hits'] > 0 and result['cmd_get'] > 0:
            result['hit'] = float(result['get_hits']) / \
                float(result['cmd_get']) * 100

        conf = public.readFile(getConf())
        result['bind'] = re.search('IP=(.+)', conf).groups()[0]
        result['port'] = int(re.search('PORT=(\d+)', conf).groups()[0])
        result['maxconn'] = int(re.search('MAXCONN=(\d+)', conf).groups()[0])
        result['cachesize'] = int(
            re.search('CACHESIZE=(\d+)', conf).groups()[0])
        return public.getJson(result)
    except Exception, e:
        return public.getJson({})


def saveConf():
     # 设置memcached缓存大小
    import re
    confFile = getConf()
    try:
        args = getArgs()
        content = public.readFile(confFile)
        content = re.sub('IP=.+', 'IP=' + args['ip'], content)
        content = re.sub('PORT=\d+', 'PORT=' + args['port'], content)
        content = re.sub('MAXCONN=\d+', 'MAXCONN=' + args['maxconn'], content)
        content = re.sub('CACHESIZE=\d+', 'CACHESIZE=' +
                         args['cachesize'], content)
        public.writeFile(confFile, content)
        reload()
        return 'ok'
    except Exception as e:
        pass
    return 'fail'


def initdStatus():
    if not app_debug:
        os_name = public.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    if os.path.exists(initd_bin):
        return 'ok'
    return 'fail'


def initdInstall():
    import shutil
    if not app_debug:
        os_name = public.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"

    mem_bin = initDreplace()
    initd_bin = getInitDFile()
    shutil.copyfile(mem_bin, initd_bin)
    public.execShell('chmod +x ' + initd_bin)
    return 'ok'


def initdUinstall():
    if not app_debug:
        os_name = public.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"
    initd_bin = getInitDFile()
    os.remove(initd_bin)
    return 'ok'

if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print status()
    elif func == 'start':
        print start()
    elif func == 'stop':
        print stop()
    elif func == 'restart':
        print restart()
    elif func == 'reload':
        print reload()
    elif func == 'initd_status':
        print initdStatus()
    elif func == 'initd_install':
        print initdInstall()
    elif func == 'initd_uninstall':
        print initdUinstall()
    elif func == 'run_info':
        print runInfo()
    elif func == 'conf':
        print getConf()
    elif func == 'save_conf':
        print saveConf()
    else:
        print 'fail'
