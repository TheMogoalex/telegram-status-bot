import datetime
import subprocess
import psutil
from typing import List, Dict, Union

class SystemInfo:
    def __init__(self, partitions: List[str]):
        self.partitions = partitions

    def get_uptime(self) -> str:
        try:
            result = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except Exception as e:
            return f"Exception: {str(e)}"
        
    def get_cpu_temperature(self) -> str:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
            return f"{temp:.2f}°C"
        except FileNotFoundError:
            return "No se pudo obtener la temperatura de la CPU"

    def get_hora(self) -> str:
        now = datetime.datetime.now()
        return now.strftime("%d-%m-%Y %H:%M")

    def get_disk_usage(self) -> List[Dict[str, Union[str, int]]]:
        disk_usage = []
        for disk in self.partitions:
            try:
                usage = psutil.disk_usage(disk)
                disk_usage.append({
                    "partition": disk,
                    "total": int(usage.total / (1024**3)),
                    "used": int(usage.used / (1024**3)),
                    "free": int(usage.free / (1024**3)),
                    "percent": int((int(usage.free / (1024**3))/int(usage.total / (1024**3))) * 100)
                })
            except Exception as e:
                disk_usage.append({
                    "partition": disk,
                    "error": str(e)
                })
        return disk_usage
