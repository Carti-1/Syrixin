import psutil

def get_ram_use():
    ram =  psutil.virtual_memory()
    return ram