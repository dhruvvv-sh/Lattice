# app/cluster/health_checker.py

from pathlib import Path

def check_disk_health (path:str)->bool:
    disk = Path(path)

    if not disk.exists():
        return False
    if not disk.is_dir():
        return False
    
    try: #checks if you can write to the disk or not
        heartbeat_file = disk/".heartbeat"
        
        with open(heartbeat_file,"w") as f:
            f.write("alive")
        with open(heartbeat_file,"r") as f:
            f.read()
        
        return True
    except Exception:
        return False
    
    


