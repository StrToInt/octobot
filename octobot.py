import logging
import random
import uuid
import configparser
import requests
import json
import math
import pprint
import traceback
import re
import os
from dataclasses import dataclass
import subprocess
import asyncio
from datetime import datetime, timedelta
from threading import Thread

from settings import OctobotSettings
from commands import OctobotCommands
from buttons import OctobotButtons

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.callback_data import CallbackData
from utils import utils
from utils import Printer_Connection,Printer_State,Print_File_Data


class Octobot:

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger('broadcast')

        self.__settings = OctobotSettings('config.yaml')
        self.__settings.reload()

        self.__bot = Bot(self.__settings.get_bot_token())
        self.__dispatcher = Dispatcher(self.__bot)
        self.__commands = OctobotCommands(self, self.__bot, self.__dispatcher, self.__settings)
        self.__buttons = OctobotButtons(self, self.__bot, self.__dispatcher, self.__settings)
        self.__print_file = None

        self.last_printer_state = 'Closed'
        self.print_file: Print_File_Data = None
        self.last_msg = None

    def get_dispatcher(self):
        return self.__dispatcher

    def get_bot(self):
        return self.__bot

    def get_settings(self):
        return self.__settings

    def get_commands(self):
        return self.__commands

    def get_last_message(self):
        return self.last_msg

    def set_last_message(self, message):
        self.last_msg = message

    def get_last_printer_state(self):
        return self.last_printer_state

    def set_last_printer_state(self, new_state):
        self.last_printer_state = new_state

    def get_print_file(self):
        return self.print_file

    def set_print_file(self, new_file):
        self.print_file = new_file



    async def send_photos(self, chat_id, silent = False, cap = None):
        make_photo()
        cam_count = config.getint('printer','cam_count')
        print(f'Make photo from {cam_count} cameras')
        if cam_count == 1:
            with open(get_image_path('photo.jpg'), 'rb') as photo:
                await bot.send_chat_action(chat_id, action = 'upload_photo')
                await bot.send_photos(chat_id,photo, caption = cap, reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent_photos') )
        else:
            media = types.MediaGroup()
            for c in range(1,cam_count+1):
                print(f'Attach photo from #{c} camera')
                media.attach_photo(types.InputFile(utils.get_image_path('photo'+str(c)+'.jpg')), caption = cap if c == 1 else None)

            await bot.send_chat_action(chat_id, action = 'upload_photo')

            try:
                await bot.send_media_group(chat_id,media, disable_notification = silent or config.getboolean('misc','silent') )
            except Exception as e:
                traceback.print_exc()
                await bot.send_message(chat_id, "\nНе удалось отправить фото", reply_markup=get_show_keyboard_button(),\
                    disable_notification = silent or config.getboolean('misc','silent') )





    #send printer status
    async def send_printer_status(self, silent = False):
        chat_id = self.__settings.get_admin()
        status = await self.get_printer_status_string()
        if status[0] == -1:
            pass
            await bot.send_message(chat_id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )
        elif status[0] == 0:
            pass
            await bot.send_message(chat_id, 'Ошибка получения статуса!\n Код ответа: '+status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )
        else:
            #send message if all success
            if  config.getint('printer','cam_count') > 0:
                await send_photos(chat_id,silent,None)

            await bot.send_message(chat_id, status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or config.getboolean('misc','silent') )


    async def delete_last_msg(self):
        global last_msg
        if last_msg != None:
            try:
                await bot.delete_message(last_msg.chat.id,last_msg.message_id)
            except:
                pass
            finally:
                last_msg = None


    async def send_actions_keyboard(self, chat_id):
        kbd = types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('🌋Прогнать файл по высотам Z', callback_data=command_cb.new(action='kb_reparse_file'))
            )
        commands_data = get_printer_commands('core')
        if commands_data.success:
            add_kbd=[]
            print(commands_data.data)
            for command in commands_data.data:
                add_kbd.append(types.InlineKeyboardButton(command['name'], callback_data=command_cb.new(action='action_core_'+command['action'])))
            kbd.add(*add_kbd)

        commands_data = get_printer_commands('custom')
        if commands_data.success:
            add_kbd=[]
            print(commands_data.data)
            for command in commands_data.data:
                add_kbd.append(types.InlineKeyboardButton(command['name'], callback_data=command_cb.new(action='action_custom_'+command['action'])))
            kbd.add(*add_kbd)

        kbd.row(
                types.InlineKeyboardButton('Назад', callback_data=command_cb.new(action='kb_show_keyboard')),
            )
        global last_msg
        last_msg = await bot.send_message(chat_id,'Действия', reply_markup=kbd)

    async def send_information_about_job_action(self, information, silent = True):
        await self.__bot.send_message(config.get('main','admin'),information)


    #send printer status
    async def send_printer_status(self, silent = False):
        chat_id = str(self.__settings.get_admin())
        status = utils.get_printer_status_string()
        if status[0] == -1:
            pass
            await self.__bot.send_message(chat_id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )
        elif status[0] == 0:
            pass
            await self.__bot.send_message(chat_id, 'Ошибка получения статуса!\n Код ответа: '+status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )
        else:
            #send message if all success
            if  self.__settings.cameras_count() > 0:
                pass
                #await send_photos(chat_id,silent,None)

            await self.__bot.send_message(chat_id, status[1], reply_markup=utils.get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )


    async def update_printer_status(self):
        current_state = ''
        job_state = None
        connection_status = utils.get_printer_connection_status()
        if connection_status.success:
            print('Printer status:' + connection_status.state)
            if connection_status.state == 'Closed':
                current_state = connection_status.state
            else:
                printer_state = utils.get_printer_state()
                if printer_state.success:
                    current_state = printer_state.data['state']['text']

                job_state = utils.get_printer_job_state()

        #Operational
        if current_state == 'Operational':
            if self.last_printer_state in ('Closed','Connecting'):
                #printer connected
                await octobot.send_information_about_job_action('⏩ Принтер подключен.')
                await octobot.send_printer_status()
                print('Printer connected')
            elif self.last_printer_state in ('Printing','Pausing','Paused','Resuming','Cancelling','Finishing'):
                #print finished
                await send_information_about_job_action('⏩ Печать завершена.')
                await send_printer_status()
                self.print_file = None
                print('Print '+job_state.data['job']['file']['name']+' finished')
        #Closed
        if current_state == 'Closed':
            if self.last_printer_state != 'Closed':
                #printer disconnected
                self.print_file = None
                await send_information_about_job_action('⏩ Принтер отключен')
                print('Printer disconnected')
        #Connecting
        elif current_state == 'Connecting':
            if self.last_printer_state == 'Closed':
                #printer connecting
                await send_information_about_job_action('⏩ Подключение к принтеру')
                print('Printer connecting')
        #Printing
        elif current_state == 'Printing':
            if self.last_printer_state == 'Printing':
                #get current z progress
                _z = get_current_z_pos(job_state.data['progress']['filepos'])
                if _z != self.print_file.last_z_pos:
                    if self.print_file.last_z_time != None:
                        self.print_file.common_layer_time = datetime.now() - self.print_file.last_z_time
                    self.print_file.last_z_time = datetime.now()
                    await send_printer_status(silent = config.getboolean('misc','silent_z_change') )
                self.print_file.last_z_pos = _z
                if (_z != -1):
                    print('Printing '+job_state.data['job']['file']['name'] + " at "+str(_z))
            elif self.last_printer_state in ('Paused','Resuming','Pausing'):
                #resumed printing file
                await send_information_about_job_action('⏩ Печать продолжена.')
                await send_printer_status()
                if self.print_file == None:
                    parse_file_for_offsets(job_state.data['job']['file']['name'])
                print('Print '+job_state.data['job']['file']['name']+' resumed')
            else: #if self.last_printer_state in ['Operational', 'Closed','Connecting']:
                #start printing file
                await send_information_about_job_action('⏩ Печать запущена. ')
                await send_printer_status()
                print('Start printing '+job_state.data['job']['file']['name'])
                parse_file_for_offsets(job_state.data['job']['file']['name'])
        #Paused
        elif current_state == 'Paused':
            if self.last_printer_state in ('Pausing','Operational'):
                #print paused
                await send_information_about_job_action('⏩ Печать приостановлена.')
                await send_printer_status()
                if self.print_file == None:
                    parse_file_for_offsets(job_state.data['job']['file']['name'])
                print('Print '+job_state.data['job']['file']['name']+' paused')
        #Pausing
        elif current_state == 'Pausing':
            if self.last_printer_state != 'Pausing':
                #print pausing
                await send_information_about_job_action('⏩ Печать ставится на паузу.')
                await send_printer_status()
                if self.print_file == None:
                    parse_file_for_offsets(job_state.data['job']['file']['name'])
                print('Print '+job_state.data['job']['file']['name']+' pausing')
        #Cancelling
        elif current_state == 'Cancelling':
            if self.last_printer_state != 'Cancelling':
                #print cancelling
                await send_information_about_job_action('⏩ Печать отменяется.')
                await send_printer_status()
                print('Print '+job_state.data['job']['file']['name']+' cancelling')
        self.last_printer_state = current_state

    async def send_information_about_job_action(self,information, silent = True):
        await self.__bot.send_message(str(self.__settings.get_admin()),information)


#config++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


config = configparser.ConfigParser()
config.read('config.ini')

#writeconfig
def config_write():
    with open('config.ini', "w") as config_file:
        config.write(config_file)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def make_photo():
    subprocess.call("bash photo.sh", shell=True)






def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(10, repeat, coro, loop)

if __name__ == '__main__':

    octobot = Octobot()

    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, octobot.update_printer_status, loop)

    executor.start_polling(octobot.get_dispatcher(), skip_updates=True)

    print('Goodbye')

