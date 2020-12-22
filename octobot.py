import logging
import random
import uuid
import typing
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

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.callback_data import CallbackData
from utils import utils
from utils import Printer_Connection,Printer_State,Print_File_Data


class Octobot:

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger('broadcast')


        self.__command_cb = CallbackData('id','action')
        self.__settings = OctobotSettings('config.yaml')
        self.__bot = Bot(self.__settings.get_bot_token())
        self.__dispatcher = Dispatcher(self.__bot)
        self.__commands_module = OctobotCommands(self, self.__bot, self.__dispatcher, self.__settings)
        self.__print_file = None

    def get_dispatcher(self):
        return self.__dispatcher

    def get_bot(self):
        return self.__bot

    def get_settings(self):
        return self.__settings


    #boolean smile
    def get_smile_for_boolean(self, inp):
        return '✅' if inp == True else '❌'

    #boolean on/off
    def get_smile_for_boolean_str(self, inp):
        return 'вкл' if inp == True else 'выкл'

    def get_additional_file_strings(self):
        info = ''

        try:
            with open('information.txt','r',encoding="utf-8") as fp:
                line = fp.readline()
                while line:
                    info += line
                    line = fp.readline()
        except:
            return None
        return info

    #get file size
    @staticmethod
    def get_file_size(path):
        try:
            return os.path.getsize(path)
        except:
            return -1

    @staticmethod
    def get_image_path(path):
        size = get_file_size(path)
        if size <= 0:
            return 'noimage.jpeg'
        else:
            return path

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
                media.attach_photo(types.InputFile(get_image_path('photo'+str(c)+'.jpg')), caption = cap if c == 1 else None)

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



#config++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


config = configparser.ConfigParser()
config.read('config.ini')

#writeconfig
def config_write():
    with open('config.ini', "w") as config_file:
        config.write(config_file)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



bot = None
dp = None

last_printer_state = 'Closed'
print_file: Print_File_Data = None
last_msg = None

command_cb = CallbackData('id','action')  # post:<id>:<action>

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def make_photo():
    subprocess.call("bash photo.sh", shell=True)




def get_settings_keyboard():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent'))+' Беззвук', callback_data=command_cb.new(action='kb_silent_toggle'))
    ).row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent_photos'))+' Беззвук на фото', callback_data=command_cb.new(action='kb_photo_silent_toggle')),
    ).row(
        types.InlineKeyboardButton(get_smile_for_boolean(config.getboolean('misc','silent_z_change'))+' Беззвук на изменение Z', callback_data=command_cb.new(action='kb_z_silent_toggle')),
    ).row(
        types.InlineKeyboardButton('Назад', callback_data=command_cb.new(action='kb_show_keyboard')),
    )

def get_show_keyboard_button():
    return types.InlineKeyboardMarkup().row(
        types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=command_cb.new(action='kb_show_keyboard')),
    )

def user_friendly_seconds(n):
    return str(timedelta(seconds = n,microseconds=0, milliseconds=0))

def str_round(number):
    return str(round(number,2))

async def update_printer_status():
    current_state = ''
    global last_printer_state,print_file
    job_state = None
    connection_status = get_printer_connection_status()
    if connection_status.success:
        print('Printer status:' + connection_status.state)
        if connection_status.state == 'Closed':
            current_state = connection_status.state
        else:
            printer_state = get_printer_state()
            if printer_state.success:
                current_state = printer_state.data['state']['text']

            job_state = get_printer_job_state()

    #Operational
    if current_state == 'Operational':
        if last_printer_state in ('Closed','Connecting'):
            #printer connected
            await send_information_about_job_action('⏩ Принтер подключен.')
            await send_printer_status()
            print('Printer connected')
        elif last_printer_state in ('Printing','Pausing','Paused','Resuming','Cancelling','Finishing'):
            #print finished
            await send_information_about_job_action('⏩ Печать завершена.')
            await send_printer_status()
            print_file = None
            print('Print '+job_state.data['job']['file']['name']+' finished')
    #Closed
    if current_state == 'Closed':
        if last_printer_state != 'Closed':
            #printer disconnected
            print_file = None
            await send_information_about_job_action('⏩ Принтер отключен')
            print('Printer disconnected')
    #Connecting
    elif current_state == 'Connecting':
        if last_printer_state == 'Closed':
            #printer connecting
            await send_information_about_job_action('⏩ Подключение к принтеру')
            print('Printer connecting')
    #Printing
    elif current_state == 'Printing':
        if last_printer_state == 'Printing':
            #get current z progress
            _z = get_current_z_pos(job_state.data['progress']['filepos'])
            if _z != print_file.last_z_pos:
                if print_file.last_z_time != None:
                    print_file.common_layer_time = datetime.now() - print_file.last_z_time
                print_file.last_z_time = datetime.now()
                await send_printer_status(silent = config.getboolean('misc','silent_z_change') )
            print_file.last_z_pos = _z
            if (_z != -1):
                print('Printing '+job_state.data['job']['file']['name'] + " at "+str(_z))
        elif last_printer_state in ('Paused','Resuming','Pausing'):
            #resumed printing file
            await send_information_about_job_action('⏩ Печать продолжена.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' resumed')
        else: #if last_printer_state in ['Operational', 'Closed','Connecting']:
            #start printing file
            await send_information_about_job_action('⏩ Печать запущена. ')
            await send_printer_status()
            print('Start printing '+job_state.data['job']['file']['name'])
            parse_file_for_offsets(job_state.data['job']['file']['name'])
    #Paused
    elif current_state == 'Paused':
        if last_printer_state in ('Pausing','Operational'):
            #print paused
            await send_information_about_job_action('⏩ Печать приостановлена.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' paused')
    #Pausing
    elif current_state == 'Pausing':
        if last_printer_state != 'Pausing':
            #print pausing
            await send_information_about_job_action('⏩ Печать ставится на паузу.')
            await send_printer_status()
            if print_file == None:
                parse_file_for_offsets(job_state.data['job']['file']['name'])
            print('Print '+job_state.data['job']['file']['name']+' pausing')
    #Cancelling
    elif current_state == 'Cancelling':
        if last_printer_state != 'Cancelling':
            #print cancelling
            await send_information_about_job_action('⏩ Печать отменяется.')
            await send_printer_status()
            print('Print '+job_state.data['job']['file']['name']+' cancelling')
    last_printer_state = current_state

async def send_information_about_job_action(information, silent = True):
    await bot.send_message(config.get('main','admin'),information)

'''
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++




#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#button "status"
@dp.callback_query_handler(command_cb.filter(action='kb_status'))
async def callback_status_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение статуса...")
        await send_printer_status()

#button "photo"
@dp.callback_query_handler(command_cb.filter(action='kb_photo'))
async def callback_photo_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("получение фото...")
        await send_photos(query.message.chat.id)

#button "show keyboard"
@dp.callback_query_handler(command_cb.filter(action='kb_show_keyboard'))
async def callback_show_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("выберите действие...")
        await start_command(query)


#button "show actions"
@dp.callback_query_handler(command_cb.filter(action='kb_show_actions'))
async def callback_show_actions_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("выберите действие...")
        await send_actions_keyboard(query.message.chat.id)

#button "show settings"
@dp.callback_query_handler(command_cb.filter(action='kb_show_settings'))
async def callback_show_settings(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("Настройки")
        await bot.send_message(query.message.chat.id,'Настройки', reply_markup=get_settings_keyboard())

#button "print"
@dp.callback_query_handler(command_cb.filter(action='kb_print'))
async def callback_show_settings(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await query.answer("Меню печати")
        kbd = types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('⏸ Начать', callback_data=command_cb.new(action='kb_print_start')),
            types.InlineKeyboardButton('⏯ Пауза', callback_data=command_cb.new(action='kb_print_start')),
            types.InlineKeyboardButton('▶️Продолжить', callback_data=command_cb.new(action='kb_print_start')),
        ).row(
            types.InlineKeyboardButton('❌ Отменить', callback_data=command_cb.new(action='kb_print_start'))
        ).row(
            types.InlineKeyboardButton('🖋Кастомная команда', callback_data=command_cb.new(action='kb_print_start'))
        )
        await bot.send_message(query.message.chat.id,'Настройки', reply_markup=kbd)

#button "silent mode toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_silent_toggle'))
async def callback_silent_mode_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent')
        config.set('misc','silent', str(val))
        config_write()
        await query.answer("Режим беззвука: " + get_smile_for_boolean_str(val))

#button "silent photo mode toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_photo_silent_toggle'))
async def callback_silent_photo_mode_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent_photos')
        config.set('misc','silent_photos', str(val))
        config_write()
        await query.answer("Режим беззвука для фотографий: " + get_smile_for_boolean_str(val))

#button "silent z change toggle"
@dp.callback_query_handler(command_cb.filter(action='kb_z_silent_toggle'))
async def callback_silent_z_change_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        val = not config.getboolean('misc','silent_z_change')
        config.set('misc','silent_z_change', str(val))
        config_write()
        await query.answer("Режим беззвука на изменение Z: " + get_smile_for_boolean_str(val))

#button "reparse file"
@dp.callback_query_handler(command_cb.filter(action='kb_reparse_file'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        job_state = get_printer_job_state()
        if job_state.success:
            await query.answer("Высчитывание высот для файла..")
            parse_file_for_offsets(job_state.data['job']['file']['name'])
            await bot.send_message(query.message.chat.id,'Высоты по файлу '+job_state.data['job']['file']['name']+' обновлены')
        else:
            await query.answer("Файл для печати не выбран!")

#button "stop request"
@dp.callback_query_handler(command_cb.filter(action='kb_stop_request'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        kbd = types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('❌ Остановить', callback_data=command_cb.new(action='kb_stop_stop')),
            types.InlineKeyboardButton('📛Выключить', callback_data=command_cb.new(action='kb_stop_shutdown')),
            types.InlineKeyboardButton('❎ Продолжить', callback_data=command_cb.new(action='kb_stop_cancel'))
            )

        last_msg = await bot.send_message(query.message.chat.id,'Запрос на выполнение команды:\n"'+c['confirm']+'"', reply_markup=kbd)

#button "stop request"
@dp.callback_query_handler(command_cb.filter(action='kb_stop_cancel'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await delete_last_msg()

#button "stop request"
@dp.callback_query_handler(command_cb.filter(action='kb_stop_stop'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await delete_last_msg()
        await execute_gcode(['G91','G0 Z10'])

        result = execute_job_command('cancel')
        if result.success:
            await bot.send_message(query.message.chat.id,'Остановка печати...')
        else:
            await bot.send_message(query.message.chat.id,'Не удалось остановить печать,\nкод ошибки: '+result.errorCode)

#button "stop request"
@dp.callback_query_handler(command_cb.filter(action='kb_stop_shutdown'))
async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    if check_user(query.message.chat.id):
        await delete_last_msg()
        await bot.send_message(query.message.chat.id,'Остановка принтера...')
        result = execute_job_command(config.get("printer", "stop_command"))

#action callback
@dp.callback_query_handler(text_contains='action_')
async def callback_action_query(query: types.CallbackQuery):
    if check_user(query.message.chat.id):
        await query.answer()
        source = None
        command = None

        global last_msg

        if query.data.startswith('id:action_core_'):
            source = 'core'
            command = query.data[len('id:action_core_'):]

        if query.data.startswith('id:action_custom_'):
            source = 'custom'
            command = query.data[len('id:action_custom_'):]

        if source != None:
            commands_data = get_printer_commands(source)
            for c in commands_data.data:
                if c['action'] == command:
                    if 'confirm' in c:
                        kbd = types.InlineKeyboardMarkup().row(
                            types.InlineKeyboardButton('Выполнить', callback_data=command_cb.new(action='actionexecute|'+source+"|"+command)),
                            types.InlineKeyboardButton('Отменить', callback_data=command_cb.new(action='actionexecute|'+'cancel'))
                            )

                        await delete_last_msg()
                        last_msg = await bot.send_message(query.message.chat.id,'Запрос на выполнение команды:\n"'+c['confirm']+'"', reply_markup=kbd)
                        print('confirmation for '+c['name']+" "+source+" "+command)
                        return
                    else:
                        await delete_last_msg()
                        result = await execute_command(source+"/"+command)

                        if result.success == True:
                            await bot.send_message(query.message.chat.id,"Команда "+c['name'] + " выполнена")
                        else:
                            await bot.send_message(query.message.chat.id,"Команда "+c['name']+' (' +source+"/"+command+ ") не выполнена\nКод ошибки:"+result.errorCode)

                        print('execute command '+c['name']+" "+source+" "+command)
                        return

#action callback
@dp.callback_query_handler(text_contains='actionexecute|')
async def callback_action_query(query: types.CallbackQuery):
    if check_user(query.message.chat.id):
        await query.answer()
        global last_msg

        if query.data.startswith('id:actionexecute|'):
            data = query.data.split('|')
            print(data)
            if len(data) == 3:
                await delete_last_msg()

                result = await execute_command(data[1]+'/'+data[2])

                if result.success == True:
                    await bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " выполнена")
                else:
                    await bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " не выполнена\nКод ошибки:"+result.errorCode)
                print('execute command '+data[1]+' '+data[2])
            elif len(data) == 2 and data[1] == 'cancel':
                await delete_last_msg()
'''
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(10, repeat, coro, loop)

if __name__ == '__main__':

    octobot = Octobot()

    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, update_printer_status, loop)

    executor.start_polling(octobot.get_dispatcher(), skip_updates=True)

    print('Goodbye')

