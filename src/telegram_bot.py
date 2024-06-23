import asyncio
from telegram import Bot
from .system_info import SystemInfo
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class TelegramBot:
    def __init__(self, token: str, chat_id: str, server_name: str, partitions: List[str]):
        self.bot = Bot(token)
        self.chat_id = chat_id
        self.server_name = server_name
        self.system_info = SystemInfo(partitions)

    async def send_message(self):
        temperatura = self.system_info.get_cpu_temperature()
        disco = self.system_info.get_disk_usage()
        hora = self.system_info.get_hora()
        uptime = self.system_info.get_uptime()
        
        mensaje = f'''{self.server_name} - Informe del Sistema\n\nHora actual: {hora} \nTemperatura CPU: {temperatura} \nUptime: {uptime} \nDiscos:'''
        for d in disco:
            mensaje += f"\n  - {d['partition']}: \n    + Total: {d['total']}GB \n    + Usado: {d['used']}GB \n    + Libre: {d['free']}GB \n    + Porcentaje libre: {d['percent']}%"
        
        await self.bot.send_message(chat_id=self.chat_id, text=mensaje)