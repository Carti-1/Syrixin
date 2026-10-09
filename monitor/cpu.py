import psutil

def get_cpu_use():
    cpu = psutil.cpu_percent(interval=1)
    return cpu
