import requests
import subprocess
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from dataclasses import dataclass
import json
from aiogram import types
from aiogram.utils.callback_data import CallbackData
import os
import re

@dataclass
class Print_File_Data:
    start_time = None
    last_z_pos = -1.0
    max_z_pos = -1.0
    last_z_time = None
    common_layer_time = None
    file_name = ''
    offsets = {}

@dataclass
class Printer_Connection:
    errorCode: str = '-1'
    success: bool = False
    state: str = 'Closed'

@dataclass
class Printer_State:
    errorCode: str = '-1'
    success: bool = False
    data: str = ''

class utils:

    callback = CallbackData('id','action')  # post:<id>:<action>
    octoprint_url = ''
    octoprint_key = ''

    @staticmethod
    def update(octoprint_url,octoprint_key):
        utils.octoprint_url = octoprint_url
        utils.octoprint_key = octoprint_key


    #parse file for Z offsets
    @staticmethod
    def parse_file_for_offsets(name, files_dir, max_z_finish):
        file_pos = 0
        max_z = -1.0
        max_z_finish = max_z_finish
        new_file_data = Print_File_Data()
        new_file_data.offsets = {}
        new_file_data.file_name = name
        new_file_data.start_time = datetime.now()
        new_file_data.common_layer_time = None
        new_file_data.last_z_time = None
        print('Parsing file for offsets: '+ name)
        with open(files_dir+name, 'r') as fp:
            for line in fp:
                last_offset = file_pos

                m = re.search(r"(?<=Z)\d+\.\d+", line)
                file_pos += len(line)
                if m:
                    res_text = m.group(0)
                    res = float(res_text) #resulted Z pos
                    try:
                        if res > max_z:
                            if max_z_finish != -1.0:
                                if res < max_z_finish:
                                    max_z = res
                            else:
                                max_z = res
                    except Exception:
                        pass

                    new_file_data.offsets.update({file_pos+len(res_text):res})
        new_file_data.max_z_pos = max_z
        print(new_file_data.offsets)
        print('max_Z = '+str(max_z))
        return new_file_data



    #get current Z pos from file with layers range
    @staticmethod
    def get_current_z_pos_with_range(offset, print_file):
        if print_file != None:
            #temp pos
            lastkey = None
            keynum = 0
            for key in print_file.offsets.keys():
                if offset <= key and lastkey != None:
                    return [print_file.offsets.get(lastkey,-1),keynum,len(print_file.offsets.keys())]
                keynum+=1
                lastkey = key
        return [-1,0,0]

    #get current Z pos from file
    @staticmethod
    def get_current_z_pos(offset,print_file):
        return utils.get_current_z_pos_with_range(offset,print_file)[0]

    #get z position as string with max and percentage
    @staticmethod
    def get_z_pos_str():
        return

    #get printer status
    @staticmethod
    def get_printer_connection_status(testmode = False):
        status = Printer_Connection()
        if testmode:
            status.success = True
            status.errorCode = 200
            status.state = 'Operational'
            return status

        try:
            r = requests.get(url = utils.octoprint_url+'/api/connection', headers = {'X-Api-Key':utils.octoprint_key}, timeout=3)
            if r.status_code == 200:
                json_data = json.loads(r.text)
                status.state = json_data['current']['state']
                status.success = True
            else:
                status.errorCode = str(r.status_code)
                status.success = False
        except Exception:
            status.success = False
        finally:
            return status

    #get printer state when connected
    @staticmethod
    def get_printer_state(testmode = False):
        state = Printer_State()

        if testmode:
            state.success = True
            state.errorCode = 200
            state.data = json.loads('{   "temperature": {     "tool0": {       "actual": 214.8821,       "target": 220.0,       "offset": 0     },     "tool1": {       "actual": 25.3,       "target": null,       "offset": 0     },     "bed": {       "actual": 50.221,       "target": 70.0,       "offset": 5     },     "history": [       {         "time": 1395651928,         "tool0": {           "actual": 214.8821,           "target": 220.0         },         "tool1": {           "actual": 25.3,           "target": null         },         "bed": {           "actual": 50.221,           "target": 70.0         }       },       {         "time": 1395651926,         "tool0": {           "actual": 212.32,           "target": 220.0         },         "tool1": {           "actual": 25.1,           "target": null         },         "bed": {           "actual": 49.1123,           "target": 70.0         }       }     ]   },   "sd": {     "ready": true   },   "state": {     "text": "Operational",     "flags": {       "operational": true,       "paused": false,       "printing": false,       "cancelling": false,  "resuming": false,       "pausing": false,       "sdReady": true,       "error": false,       "ready": true,       "closedOrError": false     }   } }')
            return state

        try:
            r = requests.get(url = utils.octoprint_url+'/api/printer', headers = {'X-Api-Key':utils.octoprint_key},timeout=3)
            if r.status_code == 200:
                state.data = json.loads(r.text)
                state.success = True
            else:
                state.errorCode = str(r.status_code)
                state.success = False
        except Exception:
            state.success = False
        finally:
            return state

    #get job state when printing
    @staticmethod
    def get_printer_job_state(testmode = False):
        job_state = Printer_State()

        if testmode:
            job_state.success = True
            job_state.errorCode = 200
            job_state.data = json.loads('{   "job": {     "file": {       "name": "whistle_v2.gcode",       "origin": "local",       "size": 1468987,       "date": 1378847754     },     "estimatedPrintTime": 8811,     "filament": {       "tool0": {         "length": 810,         "volume": 5.36       }     }   },   "progress": {     "completion": 0.2298468264184775,     "filepos": 337942,     "printTime": 276,     "printTimeLeft": 912   },   "state": "Printing" }')
            return job_state

        try:
            r = requests.get(url = utils.octoprint_url+'/api/job', headers = {'X-Api-Key':utils.octoprint_key},timeout=3)
            if r.status_code == 200:
                job_state.data = json.loads(r.text)
                if job_state.data['progress']['printTime'] == None:
                    job_state.data['progress']['printTime'] = -1
                if job_state.data['progress']['printTimeLeft'] == None:
                    job_state.data['progress']['printTimeLeft'] = -1
                job_state.success = True
            else:
                job_state.errorCode = str(r.status_code)
                job_state.success = False
        except Exception:
            job_state.success = False
        finally:
            return job_state


    #execute command
    @staticmethod
    def execute_command(path, testmode = False):
        print('Execute command '+ '/api/system/commands/'+path)
        result = Printer_State()

        if testmode:
            result.success = True
            result.errorCode = 204
            return result

        try:
            r = requests.post(url = utils.octoprint_url+'/api/system/commands/'+path, headers = {'X-Api-Key':utils.octoprint_key},timeout=8)
            if r.status_code == 204:
                result.success = True
            else:
                result.errorCode = str(r.status_code)
                result.success = False
        except Exception:
            traceback.print_exc()
            result.success = False
        finally:
            return result


    #execute command
    @staticmethod
    def execute_job_command(command):
        print('Execute job command: '+command)
        result = Printer_State()
        try:
            r = requests.post(url = utils.octoprint_url+'/job/command', json = {'command': command}, headers = {'X-Api-Key':utils.octoprint_key},timeout=8)
            if r.status_code == 204:
                result.success = True
            else:
                result.errorCode = str(r.status_code)
                result.success = False
        except Exception:
            traceback.print_exc()
            result.success = False
        finally:
            return result

    #execute gcode
    @staticmethod
    def execute_gcode(commands):
        print('Execute gcode command: '+command)
        result = Printer_State()
        try:
            r = requests.post(url = utils.octoprint_url+'/api/printer/command',json = {'commands':commands}, headers = {'X-Api-Key':utils.octoprint_key},timeout=8)
            if r.status_code == 204:
                result.success = True
            else:
                result.errorCode = str(r.status_code)
                result.success = False
        except Exception:
            traceback.print_exc()
            result.success = False
        finally:
            return result

    #get printer registered commands
    @staticmethod
    def get_printer_commands(source = 'core', testmode = False):
        printer_commands = Printer_State()

        if testmode:
            printer_commands.success = True
            printer_commands.errorCode = 200
            printer_commands.data = json.loads('[     {       "action": "shutdown",       "name": "Shutdown",       "confirm": "<strong>You are about to shutdown the system.",       "source": "core",       "resource": "http://example.com/api/system/commands/core/shutdown"     },     {       "action": "reboot",       "name": "Reboot",       "confirm": "<strong>You are about to reboot the system.om your printers internal storage).",       "source": "core",       "resource": "http://example.com/api/system/commands/core/reboot"     },     {       "action": "restart",       "name": "Restart OctoPrint",       "confirm": "<strong>You are about to restart the OctoPrint).",       "source": "core",       "resource": "http://example.com/api/system/commands/core/restart"     } ]')
            return printer_commands

        try:
            r = requests.get(url = utils.octoprint_url+'/api/system/commands/'+source, headers = {'X-Api-Key':utils.octoprint_key},timeout=5)

            if r.status_code == 200:
                printer_commands.data = json.loads(r.text)
                printer_commands.success = True
            else:
                printer_commands.errorCode = str(r.status_code)
                printer_commands.success = False
        except Exception:
            printer_commands.success = False
        finally:
            return printer_commands

    @staticmethod
    def get_additional_file_strings():
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

    def get_settings_keyboard(settings):

        return types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton(utils.get_smile_for_boolean(settings.is_silent())+' Беззвук', callback_data=utils.callback.new(action='kb_silent_toggle'))
        ).row(
            types.InlineKeyboardButton(utils.get_smile_for_boolean(settings.is_silent_z())+' Беззвук на изменение Z', callback_data=utils.callback.new(action='kb_z_silent_toggle')),
        ).row(
            types.InlineKeyboardButton('Назад', callback_data=utils.callback.new(action='kb_show_keyboard')),
        )

    @staticmethod
    def get_show_keyboard_button():

        return types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('⌨️Показать клавиатуру', callback_data=utils.callback.new(action='kb_show_keyboard')),
        )

    @staticmethod
    def user_friendly_seconds(n):
        return str(timedelta(seconds = n,microseconds=0, milliseconds=0))

    @staticmethod
    def str_round(number):
        return str(round(number,2))


    #boolean smile
    @staticmethod
    def get_smile_for_boolean(inp):
        return '✅' if inp == True else '❌'

    #boolean on/off
    @staticmethod
    def get_smile_for_boolean_str(inp):
        return 'вкл' if inp == True else 'выкл'

    #get file size
    @staticmethod
    def get_file_size(path):
        try:
            return os.path.getsize(path)
        except:
            return -1

    @staticmethod
    def get_image_path(path):
        size = utils.get_file_size(path)
        if size <= 0:
            return 'noimage.jpeg'
        else:
            return path