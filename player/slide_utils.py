import psutil
import time

WPS_PROCESS_NAMES = {
    "wps.exe",
    "et.exe",
    "wpp.exe",
    "wpscloudsvr.exe",
    "wpscenter.exe"
}

def kill_wps_processes(wait_time=0.5):
    # 第一阶段, 杀掉父进程是svchost.exe的wps进程
    for p in psutil.process_iter():
        if p.name() in WPS_PROCESS_NAMES:
            if not p.parent() is None:
                if p.parent().name() == "svchost.exe":
                    print(f"Killing process with parent of svchost.exe: {p.name()} (PID: {p.pid})")
                    p.kill()
                    time.sleep(wait_time)
    # 第二阶段, 杀掉没有父进程的进程
    for p in psutil.process_iter():
        if p.name() in WPS_PROCESS_NAMES:
            if p.parent() is None:
                print(f"Killing process with None parent: {p.name()} (PID: {p.pid})")
                p.kill()
                time.sleep(wait_time)

def get_wps_processes_relations():   
    relation = {}
    process_list = {}
    for p in psutil.process_iter():
        if p.name() in WPS_PROCESS_NAMES:
            if not p.pid in process_list:
                process_list[p.pid] = p.name()
            if not p.parent() is None:
                if not p.parent().pid in process_list:
                    process_list[p.parent().pid] = p.parent().name()
                if not p.parent().pid in relation:
                    relation[p.parent().pid] = []
                relation[p.parent().pid].append(p.pid)
            else:
                relation[-1] = [p.pid,]
    return relation, process_list
