import psutil

def get_disk_use():
    disk = psutil.disk_usage('/')
    return disk