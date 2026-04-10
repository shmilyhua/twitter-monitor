import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import List, Union

import telebot
from telebot.apihelper import ApiTelegramException
from retry import retry

from notifier_base import Message, NotifierBase


class TelegramMessage(Message):

    def __init__(self,
                 chat_id_list: List[int],
                 text: str,
                 photo_url_list: Union[List[str], None] = None,
                 video_url_list: Union[List[str], None] = None):
        super().__init__(text, photo_url_list, video_url_list)
        self.chat_id_list = chat_id_list


class TelegramNotifier(NotifierBase):
    notifier_name = 'Telegram'

    @classmethod
    def init(cls, token: str, logger_name: str):
        assert token
        cls.bot = telebot.TeleBot(token)
        cls.logger = logging.getLogger('{}'.format(logger_name))
        updates = cls._get_updates()
        cls.update_offset = updates[-1].update_id + 1 if updates else None
        cls.logger.info('Init telegram notifier succeed.')
        super().init()

    @classmethod
    @retry(Exception, delay=10, tries=10)
    def _send_message_to_single_chat(cls, chat_id: str, text: str, photo_url_list: Union[List[str], None],
                                     video_url_list: Union[List[str], None]):
        if video_url_list:
            cls.bot.send_video(chat_id=chat_id, video=video_url_list[0], caption=text, timeout=60)
        elif photo_url_list:
            if len(photo_url_list) == 1:
                cls.bot.send_photo(chat_id=chat_id, photo=photo_url_list[0], caption=text, timeout=60)
            else:
                media_group = [telebot.types.InputMediaPhoto(media=photo_url_list[0], caption=text)]
                for photo_url in photo_url_list[1:10]:
                    media_group.append(telebot.types.InputMediaPhoto(media=photo_url))
                cls.bot.send_media_group(chat_id=chat_id, media=media_group, timeout=60)
        else:
            cls.bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True, timeout=60)

    @classmethod
    def send_message(cls, message: TelegramMessage):
        assert cls.initialized
        assert isinstance(message, TelegramMessage)
        for chat_id in message.chat_id_list:
            try:
                cls._send_message_to_single_chat(chat_id, message.text, message.photo_url_list, message.video_url_list)
            except ApiTelegramException as e:
                cls.logger.error('{}, trying to send message without media.'.format(e))
                cls._send_message_to_single_chat(chat_id, message.text, None, None)

    @classmethod
    @retry(Exception, delay=60)
    def _get_updates(cls, offset=None) -> List[telebot.types.Update]:
        return cls.bot.get_updates(offset=offset)

    @classmethod
    def _get_new_updates(cls) -> List[telebot.types.Update]:
        updates = cls._get_updates(offset=cls.update_offset)
        if updates:
            cls.update_offset = updates[-1].update_id + 1
        return updates

    @classmethod
    def confirm(cls, message: TelegramMessage) -> bool:
        assert cls.initialized
        assert isinstance(message, TelegramMessage)
        message.text = '{}\nPlease reply Y/N'.format(message.text)
        cls.put_message_into_queue(message)
        sending_time = datetime.now(timezone.utc)
        
        while True:
            for update in cls._get_new_updates():
                received_message = update.message
                if not received_message:
                    continue
                
                message_date = datetime.fromtimestamp(received_message.date, timezone.utc)
                if message_date < sending_time:
                    continue
                if received_message.chat.id not in message.chat_id_list:
                    continue
                
                text = (received_message.text or '').upper()
                if text == 'Y':
                    return True
                if text == 'N':
                    return False
            time.sleep(10)

    @classmethod
    def listen_exit_command(cls, chat_id: str):

        def _listen_exit_command():
            starting_time = datetime.now(timezone.utc)
            while True:
                for update in cls._get_new_updates():
                    received_message = update.message
                    if not received_message:
                        continue
                    
                    message_date = datetime.fromtimestamp(received_message.date, timezone.utc)
                    if message_date < starting_time:
                        continue
                    if received_message.chat.id != chat_id:
                        continue
                    
                    text = (received_message.text or '').upper()
                    if text == 'EXIT':
                        if cls.confirm(TelegramMessage([chat_id], 'Do you want to exit the program?')):
                            cls.put_message_into_queue(TelegramMessage([chat_id], 'Program will exit after 5 sec.'))
                            cls.logger.error('The program exits by the telegram command')
                            time.sleep(5)
                            os._exit(0)
                time.sleep(20)

        threading.Thread(target=_listen_exit_command, daemon=True).start()


def send_alert(token: str, chat_id: int, message: str):
    bot = telebot.TeleBot(token)
    bot.send_message(chat_id=chat_id, text=message, timeout=60)
