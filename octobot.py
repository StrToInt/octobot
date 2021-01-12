import logging
import random
import uuid
import configparser
import requests
import json
import math
import pprint
import traceback
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
        utils.update(self.__settings.getOctoprintURL(),self.__settings.getOctoprintKEY())

        self.last_printer_state = 'Closed'
        self.print_file: Print_File_Data = None
        self.last_msg = None
        self.cooldown_marker = False
        self.last_bed_temp = -1.0

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
        self.make_photo()
        await self.__bot.send_chat_action(chat_id, action = 'upload_photo')

        try:
            with open(utils.get_image_path(self.__settings.get_photo_file()), 'rb') as photo:
                await self.__bot.send_photo(chat_id,photo, caption = cap, disable_notification = silent or self.__settings.is_silent(), reply_markup=utils.get_show_keyboard_button())
        except Exception as e:
            traceback.print_exc()
            await self.__bot.send_message(chat_id, "\nНе удалось отправить фото\n"+cap, reply_markup=utils.get_show_keyboard_button(),\
                disable_notification = silent or self.__settings.is_silent() )



    #get printer status text
    def get_printer_status_string(self, addition_message = None, _connection_status = None, _printer_state = None, _job_state = None):
        photo_cation = 'Фото '
        global print_file
        connection_status = utils.get_printer_connection_status() if _connection_status == None else _connection_status
        msg = datetime.now().strftime('%d.%m.%Y %H:%M:%S')+'\n'
        if connection_status.success:
            if connection_status.state in ['Closed','Offline']:
                msg += '❌ Принтер выключен'
                print('11111')
            else:
                msg += '✅ Принтер включен\n'

                if addition_message != None:
                    msg += addition_message+"\n"
                printer_state = utils.get_printer_state() if _printer_state == None else _printer_state
                if printer_state.success:
                    msg += '🔥Стол: ' + utils.str_round(printer_state.data['temperature']['bed']['actual'])+'° / '+\
                                        utils.str_round(printer_state.data['temperature']['bed']['target'])+'° Δ'+\
                                        utils.str_round(printer_state.data['temperature']['bed']['offset'])+'°'+'\n'
                    msg += '🔥Экструдер: '+ utils.str_round(printer_state.data['temperature']['tool0']['actual'])+'° / '+\
                                            utils.str_round(printer_state.data['temperature']['tool0']['target'])+'°? Δ'+\
                                            utils.str_round(printer_state.data['temperature']['tool0']['offset'])+'°'+'\n'
                    if ( (printer_state.data['state']['flags']['printing'] == True) or
                    (printer_state.data['state']['flags']['pausing'] == True) or
                    (printer_state.data['state']['flags']['paused'] == True) or
                    (printer_state.data['state']['flags']['resuming'] == True) or
                    (printer_state.data['state']['flags']['cancelling'] == True) ):
                        #get job state if printing
                        job_state = utils.get_printer_job_state() if _job_state == None else _job_state
                        if job_state.success:

                            msg += '🖨Принтер '
                            if printer_state.data['state']['flags']['printing']:
                                msg += 'печатает'
                            elif printer_state.data['state']['flags']['pausing']:
                                msg += 'приостанавливает печать'
                            elif printer_state.data['state']['flags']['paused']:
                                msg += 'на паузе'
                            elif printer_state.data['state']['flags']['resuming']:
                                msg += 'возобновляет печать'
                            elif printer_state.data['state']['flags']['cancelling']:
                                msg += 'отменяет печать'
                            msg += '\n'

                            msg += '💾Файл: '+job_state.data['job']['file']['name']
                            if self.print_file != None:
                                if self.print_file.start_time != None:
                                    msg += '\n⏱ Печать начата: '+self.print_file.start_time.strftime('%d.%m.%Y %H:%M')
                            if job_state.data['job']['estimatedPrintTime'] != None:
                                msg += '\n⏱ Расчетное время печати: '+utils.user_friendly_seconds(job_state.data['job']['estimatedPrintTime'])
                            _z = utils.get_current_z_pos_with_range(job_state.data['progress']['filepos'],self.print_file)

                            if self.print_file != None:
                                if _z[0] != -1:
                                    photo_cation ='Высота: '+str(round(_z[0],2)) + " / " +str(round(self.print_file.max_z_pos,2)) + "мм " +\
                                        str(round(100*_z[0]/self.print_file.max_z_pos,1))+"% Осталось: "+str(round(self.print_file.max_z_pos-_z[0],2))+"мм"+\
                                        "\n📚Слой "+str(_z[1]) + " / "+str(_z[2])+" "+str(round(100*_z[1]/_z[2],1))+"% Осталось: "+str(_z[2]-_z[1])
                                    if self.print_file.common_layer_time != None:
                                        photo_cation += "\n⏱/📚Время на слой "+str(self.print_file.common_layer_time).split('.')[0]
                                    msg += '\n🏔'+photo_cation
                                else:
                                    msg += '\n🏔Высота Z ?'
                            if job_state.data['job']['filament'] != None:
                                msg += '\n⛓Израсходуется: '+str(round(job_state.data['job']['filament']['tool0']['length'],2))+' мм / '+str(round(job_state.data['job']['filament']['tool0']['volume'],2))+' см³'
                            tempp = '\n🔄Прогресс: ' + str(job_state.data['progress']['filepos'])+' / ' +\
                                str(job_state.data['job']['file']['size'])+' байт '+\
                                str(round(job_state.data['progress']['completion'],2))+' %'
                            photo_cation += tempp
                            msg += tempp
                            msg += '\n⏰ Время печати: '+utils.user_friendly_seconds(job_state.data['progress']['printTime'])
                            msg += '\n⏰ Осталось: '+utils.user_friendly_seconds(job_state.data['progress']['printTimeLeft'])
                            time_end = datetime.now() + timedelta(seconds = job_state.data['progress']['printTimeLeft'])
                            msg += '\n⏰ Закончится: '+time_end.strftime('%d.%m.%Y %H:%M')
                        else:
                            msg += '🆘Ошибка получения данных о печати'
                else:
                    msg += '🆘Ошибка получения данных о статусе'

                add_info = utils.get_additional_file_strings()
                if add_info != None:
                    msg += '\n'+add_info

                return [1,msg]

            add_info = utils.get_additional_file_strings()
            if add_info != None:
                msg += '\n'+add_info
            return [1,msg]
        else:
            return [0,connection_status.errorCode]

        return [-1,'']

    #send printer status
    async def send_printer_status(self, silent = False, onlystatus = False, addition_message = None, _connection_status = None, _printer_state = None, _job_state = None):
        chat_id = self.__settings.get_admin()
        status = self.get_printer_status_string(addition_message, _connection_status, _printer_state, _job_state)
        if status[0] == -1:
            await self.__bot.send_message(chat_id, 'Подключение к OCTOPRINT не удалось', reply_markup=get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )
        elif status[0] == 0:
            await self.__bot.send_message(chat_id, 'Ошибка получения статуса!\n Код ответа: '+status[1], reply_markup=get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )
        else:
            #send message if all success
            if (self.__settings.is_photo_enabled() and onlystatus == False):
                await self.send_photos(chat_id,silent or self.__settings.is_silent() ,status[1])
            else:
                await self.__bot.send_message(chat_id, status[1], reply_markup=utils.get_show_keyboard_button(), disable_notification = silent or self.__settings.is_silent() )


    async def delete_last_msg(self, message = None):
        if self.last_msg != None:
            try:
                if message == None:
                    await self.__bot.delete_message(self.last_msg.chat.id,self.last_msg.message_id)
                else:
                    await self.__bot.delete_message(message.chat.id,message.message_id)
            except:
                pass
            finally:
                self.set_last_message(None)


    async def send_actions_keyboard(self, chat_id):
        kbd = types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('🌋Прогнать файл по высотам Z', callback_data=utils.callback.new(action='kb_reparse_file'))
            )

        kbd.row(
                types.InlineKeyboardButton('♻️ Подключить', callback_data=utils.callback.new(action='kb_con_connect')),
                types.InlineKeyboardButton('♻️ Отключить', callback_data=utils.callback.new(action='kb_con_disconnect')),
            )
        commands_data = utils.get_printer_commands('core')
        if commands_data.success:
            add_kbd=[]
            print(commands_data.data)
            for command in commands_data.data:
                add_kbd.append(types.InlineKeyboardButton(command['name'], callback_data=utils.callback.new(action='action_core_'+command['action'])))
            kbd.add(*add_kbd)

        commands_data = utils.get_printer_commands('custom')
        if commands_data.success:
            add_kbd=[]
            print(commands_data.data)
            for command in commands_data.data:
                kbd.row(types.InlineKeyboardButton(command['name'], callback_data=utils.callback.new(action='action_custom_'+command['action'])))

        kbd.row(
                types.InlineKeyboardButton('Назад', callback_data=utils.callback.new(action='kb_show_keyboard')),
            )
        await self.delete_last_msg()
        self.set_last_message(await self.__bot.send_message(chat_id,'Действия', reply_markup=kbd))

    async def update_printer_status(self):
        current_state = ''

        job_state = utils.get_printer_job_state()
        connection_status = utils.get_printer_connection_status()
        printer_state = utils.get_printer_state()

        last_state = self.last_printer_state
        if connection_status.success:
            print('Printer status:' + connection_status.state)
            if connection_status.state == 'Closed':
                current_state = connection_status.state
            else:
                if printer_state.success:
                    current_state = printer_state.data['state']['text']


        self.last_printer_state = current_state

        print('Last state: '+last_state)

        #Operational
        if current_state == 'Operational':
            if last_state in ('Closed','Connecting'):
                #printer connected
                #await self.__bot.send_message(self.__settings.get_admin(), '⏩ Принтер подключен.', disable_notification = self.__settings.is_silent() )
                await self.send_printer_status(False, False, '🔴 #Принтер подключен', connection_status, printer_state, job_state)
                print('Printer connected')
            elif last_state in ('Printing','Pausing','Paused','Resuming','Cancelling','Finishing'):
                #print finished
                #await self.__bot.send_message(self.__settings.get_admin(), '⏩ Печать завершена.', disable_notification = self.__settings.is_silent() )
                await self.send_printer_status(True if self.__settings.get_cooldown_temp() != -1 else False, False, '🔴 #Печать завершена', connection_status, printer_state, job_state)
                #await self.send_printer_status()
                self.print_file = None
                print('Print '+job_state.data['job']['file']['name']+' finished')

            if self.__settings.get_cooldown_temp() != -1:
                if printer_state.success:
                    bed_temp = printer_state.data['temperature']['bed']['actual']
                    if self.last_bed_temp != -1:
                        if bed_temp < self.last_bed_temp:
                            await self.send_printer_status(False, False, '🔴 #Печать завершена, стол охладился', connection_status, printer_state, job_state)
                    self.last_bed_temp = bed_temp
        #Closed
        if current_state == 'Closed':
            if last_state != 'Closed':
                #printer disconnected
                self.print_file = None
                await self.send_printer_status(False, False, '🔴 #Принтер отключен', connection_status, printer_state, job_state)
                print('Printer disconnected')
        #Connecting
        elif current_state == 'Connecting':
            if last_state == 'Closed':
                #printer connecting
                await self.send_printer_status(False, False, '🔴 #Подключение к принтеру...', connection_status, printer_state, job_state)
                print('Printer connecting')
        #Printing
        elif current_state == 'Printing':
            if last_state == 'Printing':
                #get current z progress
                pos = utils.get_current_z_pos_with_range(job_state.data['progress']['filepos'],self.print_file)

                _z = pos[0]
                _layer = pos[1]

                last_z = self.print_file.last_z_pos
                last_layer = self.print_file.last_layer

                self.print_file.last_z_pos = _z
                self.print_file.last_layer = _layer

                if _layer != last_layer:
                    if self.print_file.last_z_time != None:
                        layer_delta = _layer - last_layer
                        seconds = datetime.now() - self.print_file.last_z_time
                        seconds_per_layer = int(round(seconds.total_seconds() / layer_delta))
                        print('seconds_per_layer: '+str(seconds_per_layer)+ " "+str(seconds)+ ' '+str(layer_delta))
                        self.print_file.common_layer_time = timedelta(seconds = seconds_per_layer)
                    self.print_file.last_z_time = datetime.now()
                    await self.send_printer_status(self.__settings.is_silent_z(), False, None, connection_status, printer_state, job_state)
                    print('printing at: layer '+str(_layer)+" z_pos: "+str(_z))

            elif last_state in ('Paused','Resuming','Pausing'):
                #resumed printing file
                await self.send_printer_status(False, False, '🔴 #Печать продолжена', connection_status, printer_state, job_state)
                #await self.send_printer_status()
            else: #if last_state in ['Operational', 'Closed','Connecting']:
                #start printing file
                await self.send_printer_status(False, False, '🔴 #Печать запущена', connection_status, printer_state, job_state)
                #await self.send_printer_status()
                self.print_file = utils.parse_file_for_offsets(job_state.data['job']['file']['name'],self.__settings.get_files_dir(),self.__settings.get_max_z_finish())
        #Paused
        elif current_state == 'Paused':
            if last_state in ('Pausing','Operational'):
                #print paused
                await self.send_printer_status(False, False, '🔴 #Печать приостановлена', connection_status, printer_state, job_state)
                #await self.send_printer_status()
        #Pausing
        elif current_state == 'Pausing':
            if last_state != 'Pausing':
                #print pausing
                await self.send_printer_status(False, False, '🔴 #Печать ставится на паузу', connection_status, printer_state, job_state)
                #await self.send_printer_status()
        #Cancelling
        elif current_state == 'Cancelling':
            if last_state != 'Cancelling':
                #print cancelling
                await self.send_printer_status(False, False, '🔴 #Печать отменяется', connection_status, printer_state, job_state)
                #await self.send_printer_status()

    #config++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def make_photo(self):
        subprocess.call(self.__settings.get_photo_script(), shell=True)

def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(15, repeat, coro, loop)

if __name__ == '__main__':

    octobot = Octobot()

    loop = asyncio.get_event_loop()
    loop.call_later(15, repeat, octobot.update_printer_status, loop)

    executor.start_polling(octobot.get_dispatcher(), skip_updates=True)

    print('Goodbye')

