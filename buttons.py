from aiogram import Bot, Dispatcher, executor, types
from settings import OctobotSettings
from aiogram.utils.callback_data import CallbackData
from utils import utils
from aiogram import types
import typing

class OctobotButtons:


    def __init__(self, octobot, bot, dispatcher, settings: OctobotSettings):
        self.__octobot = octobot
        self.__bot = bot
        self.__settings = settings
        self.__dispatcher = dispatcher


        #button "status"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_status'))
        async def callback_status_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await query.answer("получение статуса...")
                await self.__octobot.send_printer_status()

        #button "photo"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_photo'))
        async def callback_photo_command(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await query.answer("получение фото...")
                await self.__octobot.send_photos(query.message.chat.id)

        #button "show keyboard"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_show_keyboard'))
        async def callback_show_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                await query.answer("выберите действие...")
                await self.__octobot.get_commands().show_start_keyboard(query)


        #button "show actions"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_show_actions'))
        async def callback_show_actions_keyboard(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await query.answer("выберите действие...")
                await self.__octobot.delete_last_msg(query.message)
                await self.__octobot.send_actions_keyboard(query.message.chat.id)

        #button "show settings"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_show_settings'))
        async def callback_show_settings(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await query.answer("Настройки")
                await self.__octobot.delete_last_msg(query.message)
                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Настройки', reply_markup=utils.get_settings_keyboard(self.__settings)))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #button "print"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_print'))
        async def callback_print(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await query.answer("Меню печати")
                await self.__octobot.delete_last_msg(query.message)
                kbd = types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton('⏸ Начать', callback_data=utils.callback.new(action='kb_print_start')),
                    types.InlineKeyboardButton('⏯ Пауза', callback_data=utils.callback.new(action='kb_print_pause')),
                    types.InlineKeyboardButton('▶️Продолжить', callback_data=utils.callback.new(action='kb_print_resume')),
                ).row(
                    types.InlineKeyboardButton('❌ Отменить', callback_data=utils.callback.new(action='kb_print_cancel'))
                ).row(
                    types.InlineKeyboardButton('❌ Выбрать файл...', callback_data=utils.callback.new(action='kb_print_select_file')),
                ).row(
                    types.InlineKeyboardButton('🖋Кастомная команда', callback_data=utils.callback.new(action='kb_custom_g_code'))
                ).row(
                    types.InlineKeyboardButton('Назад', callback_data=utils.callback.new(action='kb_show_keyboard')),
                )

                self.__octobot.set_last_message((await bot.send_message(query.message.chat.id,'Настройки', reply_markup=kbd)))


        #button get list files
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_print_select_file'))
        async def callback_print(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                result = utils.get_list_files()

                if result.success:
                    kbd = types.InlineKeyboardMarkup()

                    for file in result.data['files']:
                        if file['type'] == 'machinecode':
                            kbd.row(types.InlineKeyboardButton(file['name'], callback_data=utils.callback.new(action='kb_print_choose_'+file['name'])))


                    await bot.send_message(query.message.chat.id,'Выберите файл для печати:', reply_markup = kbd)
                else:
                    await bot.send_message(query.message.chat.id,'Не удалось получить список файлов,\nкод ошибки: '+result.errorCode)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #button "silent mode toggle"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_silent_toggle'))
        async def callback_silent_mode_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                self.__settings.toggle_silent()
                await query.answer("Режим беззвука: " + utils.get_smile_for_boolean_str(self.__settings.is_silent_z()))
                await self.__octobot.delete_last_msg(query.message)
                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Настройки', reply_markup=utils.get_settings_keyboard(self.__settings)))

        #button "silent z change toggle"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_z_silent_toggle'))
        async def callback_silent_z_change_toggle(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                val = self.__settings.toggle_silent_z()
                await self.__octobot.delete_last_msg(query.message)
                await query.answer("Режим беззвука на изменение Z: " + utils.get_smile_for_boolean_str(val))
                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Настройки', reply_markup=utils.get_settings_keyboard(self.__settings)))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #button "reparse file"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_reparse_file'))
        async def callback_reparse_file(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                job_state = get_printer_job_state()
                if job_state.success:
                    await query.answer("Высчитывание высот для файла..")
                    parse_file_for_offsets(job_state.data['job']['file']['name'])
                    await bot.send_message(query.message.chat.id,'Высоты по файлу '+job_state.data['job']['file']['name']+' обновлены')
                else:
                    await query.answer("Файл для печати не выбран!")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_request'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                btns = [types.InlineKeyboardButton('⏸ Пауза', callback_data=utils.callback.new(action='kb_stop_pause')),
                        types.InlineKeyboardButton('❌ Отменить', callback_data=utils.callback.new(action='kb_stop_stop_request'))]
                if self.__settings.is_abort_command_enabled():
                    btns.append(types.InlineKeyboardButton('📛Выключить', callback_data=utils.callback.new(action='kb_stop_shutdown_request')))

                kbd = types.InlineKeyboardMarkup().row(*btns)

                kbd.row(
                        types.InlineKeyboardButton('Назад', callback_data=utils.callback.new(action='kb_show_keyboard')),
                    )

                await self.__octobot.delete_last_msg(query.message)
                self.__octobot.set_last_message(await bot.send_message(query.message.chat.id,'Остановка принтера:', reply_markup=kbd))

        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_pause'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)

                result = utils.issue_job_command('pause')
                if result.success:
                    await bot.send_message(query.message.chat.id,'Команда выполнена: приостановить печать')
                else:
                    await bot.send_message(query.message.chat.id,'Не удалось приостановить печать,\nкод ошибки: '+result.errorCode)

        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_stop_request'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)

                kbd = types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton('Выполнить', callback_data=utils.callback.new(action='kb_stop_stop')),
                    types.InlineKeyboardButton('Отменить', callback_data=utils.callback.new(action='kb_show_keyboard'))
                    )
                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Отменить печать?', reply_markup=kbd))

        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_shutdown_request'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                kbd = types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton('Выполнить', callback_data=utils.callback.new(action='kb_stop_shutdown')),
                    types.InlineKeyboardButton('Отменить', callback_data=utils.callback.new(action='kb_show_keyboard'))
                    )
                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Экстренный стоп?', reply_markup=kbd))

        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_stop'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)

                result = utils.issue_job_command('cancel')
                utils.execute_gcode(['G91','G0 Z10','M84'])

                if result.success:
                    await bot.send_message(query.message.chat.id,'Команда выполнена: отменить печать')
                else:
                    await bot.send_message(query.message.chat.id,'Не удалось отменить печать,\nкод ошибки: '+result.errorCode)


        #button "stop request"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_stop_shutdown'))
        async def callback_stop(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)

                result = utils.execute_command(self.__settings.get_abort_command())

                if result.success == True:
                    await self.__bot.send_message(query.message.chat.id,"Остановка принтера...")
                else:
                    await self.__bot.send_message(query.message.chat.id,"Команда не выполнена\nКод ошибки:"+result.errorCode)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #button "connection"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_con_connect'))
        async def callback_connection(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                result = utils.connect_printer(issue_connect = True)
                if result.success:
                    await bot.send_message(query.message.chat.id,'Команда выполнена: Принтер подключен')
                else:
                    await bot.send_message(query.message.chat.id,'Не удалось подключиться,\nкод ошибки: '+result.errorCode)

        #button "connection"
        @dispatcher.callback_query_handler(utils.callback.filter(action='kb_con_disconnect'))
        async def callback_connection(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
            if self.check_user(query.message.chat.id):
                await self.__octobot.delete_last_msg(query.message)
                result = utils.connect_printer(issue_connect = True)
                if result.success:
                    await bot.send_message(query.message.chat.id,'КОманда выполнена: Принтер отключен')
                else:
                    await bot.send_message(query.message.chat.id,'Не удалось отключиться,\nкод ошибки: '+result.errorCode)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #action callback
        @dispatcher.callback_query_handler(text_contains='action_')
        async def callback_action_query(query: types.CallbackQuery):
            if self.check_user(query.message.chat.id):
                await query.answer()
                source = None
                command = None

                await self.__octobot.delete_last_msg(query.message)

                if query.data.startswith('id:action_core_'):
                    source = 'core'
                    command = query.data[len('id:action_core_'):]

                if query.data.startswith('id:action_custom_'):
                    source = 'custom'
                    command = query.data[len('id:action_custom_'):]

                if source != None:
                    commands_data = utils.get_printer_commands(source)
                    for c in commands_data.data:
                        if c['action'] == command:
                            if 'confirm' in c:
                                kbd = types.InlineKeyboardMarkup().row(
                                    types.InlineKeyboardButton('Выполнить', callback_data=utils.callback.new(action='actionexecute|'+source+"|"+command)),
                                    types.InlineKeyboardButton('Отменить', callback_data=utils.callback.new(action='actionexecute|'+'cancel'))
                                    )

                                self.__octobot.set_last_message(await self.__bot.send_message(query.message.chat.id,'Запрос на выполнение команды:\n"'+c['confirm']+'"', reply_markup=kbd))
                                print('confirmation for '+c['name']+" "+source+" "+command)
                                return
                            else:
                                result = utils.execute_command(source+"/"+command)

                                if result.success == True:
                                    await self.__bot.send_message(query.message.chat.id,"Команда "+c['name'] + " выполнена")
                                else:
                                    await self.__bot.send_message(query.message.chat.id,"Команда "+c['name']+' (' +source+"/"+command+ ") не выполнена\nКод ошибки:"+result.errorCode)

                                print('execute command '+c['name']+" "+source+" "+command)
                                return

        #action callback
        @dispatcher.callback_query_handler(text_contains='actionexecute|')
        async def callback_action_query(query: types.CallbackQuery):
            if self.check_user(query.message.chat.id):
                await query.answer()
                await self.__octobot.delete_last_msg(query.message)

                if query.data.startswith('id:actionexecute|'):
                    data = query.data.split('|')
                    print(data)
                    if len(data) == 3:
                        result = utils.execute_command(data[1]+'/'+data[2])

                        if result.success == True:
                            await self.__bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " выполнена")
                        else:
                            await self.__bot.send_message(query.message.chat.id,"Команда "+data[1]+'/'+data[2] + " не выполнена\nКод ошибки:"+result.errorCode)
                        print('execute command '+data[1]+' '+data[2])
                    elif len(data) == 2 and data[1] == 'cancel':
                        await self.__octobot.send_actions_keyboard(query.message.chat.id)
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    def check_user(self, user_id):
        return self.__settings.check_user(user_id)

