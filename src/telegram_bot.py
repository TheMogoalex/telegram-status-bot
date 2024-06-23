import asyncio
from telegram import Bot
from .system_info import SystemInfo
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class TelegramBot:
    def __init__(self, token: str, chat_id: str, server_name: str, partitions: List[str], language: str):
        self.bot = Bot(token)
        self.chat_id = chat_id
        self.server_name = server_name
        self.system_info = SystemInfo(partitions)
        self.language = language

    def format_message(self) -> str:
        temperatura = self.system_info.get_cpu_temperature()
        disco = self.system_info.get_disk_usage()
        hora = self.system_info.get_hora()
        uptime = self.system_info.get_uptime()

        if self.language == 'es':
            mensaje = f'''{self.server_name} - Informe del Sistema\n\nHora actual: {hora} \nTemperatura CPU: {temperatura} \nUptime: {uptime} \nDiscos:'''
            for d in disco:
                mensaje += f"\n  - {d['partition']}: \n    + Total: {d['total']}GB \n    + Usado: {d['used']}GB \n    + Libre: {d['free']}GB \n    + Porcentaje libre: {d['percent']}%"
        else:  
            mensaje = f'''{self.server_name} - System Report\n\nCurrent time: {hora} \nCPU Temperature: {temperatura} \nUptime: {uptime} \nDisks:'''
            for d in disco:
                mensaje += f"\n  - {d['partition']}: \n    + Total: {d['total']}GB \n    + Used: {d['used']}GB \n    + Free: {d['free']}GB \n    + Free Percentage: {d['percent']}%"

        return mensaje

    async def send_message(self):
        mensaje = self.format_message()
        await self.bot.send_message(chat_id=self.chat_id, text=mensaje)
