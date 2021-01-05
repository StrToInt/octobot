from aiogram import types
from settings import OctobotSettings
from aiogram.utils.callback_data import CallbackData
from utils import utils

class OctobotCommands:


    def __init__(self, octobot, bot, dispatcher, settings: OctobotSettings):
        self.__octobot = octobot
        self.__bot = bot
        self.__settings = settings
        self.__dispatcher = dispatcher

        #command /start. show all menus
        @dispatcher.message_handler(commands=['start'])
        async def start_command(message: types.Message):
            await self.show_start_keyboard(message)

        #command /photo. get photo
        @dispatcher.message_handler(commands=['photo'])
        async def photo_command(message: types.Message):
            if self.check_user(message.from_user.id):
                await self.__octobot.send_photos(message.from_user.id, silent = False, cap = None)

        #command /status. get status
        @dispatcher.message_handler(commands=['status'])
        async def status_command(message: types.Message):
            if self.check_user(message.from_user.id):
                await self.__octobot.send_printer_status(silent = False)

        #command /actions. get actions
        @dispatcher.message_handler(commands=['actions'])
        async def actions_command(message: types.Message):
            if self.check_user(message.from_user.id):
                await self.__octobot.send_actions_keyboard(message.from_user.id)

        #echo all
        @dispatcher.message_handler()
        async def echo(message: types.Message):
            await message.answer(message.text + "\nYou ID: "+ str(message.from_user.id))

    async def show_start_keyboard(self, message):
        if self.check_user(message.from_user.id):
            self.__octobot.set_last_message(await self.__bot.send_message(message.from_user.id,'Выберите действие', reply_markup=self.get_main_keyboard()))

    def get_main_keyboard(self):
        return types.InlineKeyboardMarkup().row(
            types.InlineKeyboardButton('❔ Статус', callback_data=utils.callback.new(action='kb_status')),
            types.InlineKeyboardButton('📸Фото', callback_data=utils.callback.new(action='kb_photo')),
            types.InlineKeyboardButton('🖨Печать...', callback_data=utils.callback.new(action='kb_print')),
        ).add(types.InlineKeyboardButton('📛STOP...', callback_data=utils.callback.new(action='kb_stop_request'))).row(
            types.InlineKeyboardButton('� Настройки', callback_data=utils.callback.new(action='kb_show_settings')),
            types.InlineKeyboardButton(utils.get_smile_for_boolean(self.__settings.is_silent())+' Silent', callback_data=utils.callback.new(action='kb_silent_toggle')),
            types.InlineKeyboardButton('📲Действия', callback_data=utils.callback.new(action='kb_show_actions')),
        )

    def check_user(self, user_id):
        return self.__settings.check_user(user_id)

