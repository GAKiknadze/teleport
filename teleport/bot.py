# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz
from pyrogram import Client, Filters, Message


from extractor import apply_emoji_filter, extract_from_text, \
    save_today_actual_xls, delete_extract_container_folder
from settings import \
    USER_NAME, API_ID, API_HASH, DATE_WITH_TIME_FORMAT, HANDLED_CHATS

logging.basicConfig(
    filename='logs/%s.txt' % datetime.today().strftime(DATE_WITH_TIME_FORMAT),
    level=logging.INFO,
    format='[%(asctime)s:%(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Client(USER_NAME, api_id=API_ID, api_hash=API_HASH)


def get_chat_name(message: Message) -> str:
    first_name = message.chat.first_name
    if first_name:
        return first_name
    title = message.chat.title
    if title:
        return title
    forward_sender = message.forward_sender_name
    if forward_sender:
        return forward_sender
    return '*chat name not found*'


def extractor_from_message(message: Message) -> list:
    try:
        text = message.text
        if not text:
            text = message.caption
            if not text:
                raise Exception('Message without text')
        owner = message.from_user
        if owner:
            owner = owner.id
        else:
            owner = message.chat.id
        return extract_from_text(
            apply_emoji_filter(text),
            message.chat.id,
            owner
        )
    except Exception as e:
        logging.exception(e)
        return []


def force_in_mem_update_today_extract_for_chat(chat_id):
    today_date = datetime.utcnow().date()
    delete_extract_container_folder(chat_id)
    today_extract = []
    for message in app.iter_history(chat_id):
        tmp_date = datetime.utcfromtimestamp(message.date).date()
        if tmp_date == today_date:
            today_extract.extend(extractor_from_message(message))
        else:
            break
    save_today_actual_xls(today_extract, chat_id)


def get_msk_formatted_time(datetime) -> str:
    moscow_tz = pytz.timezone('Europe/Moscow')
    edit_time = datetime.fromtimestamp(datetime, tz=moscow_tz)
    return edit_time.strftime('%m-%d %H:%M:%S')


def force_in_mem_today_actual_for_all():
    logging.info('Today all started')
    for handled_chat_id in HANDLED_CHATS:
        logging.info('Today %s started' % handled_chat_id)
        try:
            force_in_mem_update_today_extract_for_chat(handled_chat_id)
        except Exception as e:
            logging.exception(e)
    logging.info('Today all finish')


@app.on_deleted_messages()
def on_messages_delete(client, messages):
    if len(messages) > 0:
        force_in_mem_today_actual_for_all()


@app.on_message(Filters.edited)
def on_message_edited(client, message):
    chat_id = message.chat.id
    if chat_id in HANDLED_CHATS:
        users = HANDLED_CHATS[chat_id]
        for to in users:
            try:
                if to == chat_id:
                    forwarded_message = message
                else:
                    forwarded_message = message.forward(chat_id=to, as_copy=True)
                msk_ftime = get_msk_formatted_time(message.edit_date)
                forwarded_message.reply_text('Изменено в "%s"' % msk_ftime)
            except Exception:
                logging.error('Error when forward to %s' % to)
        tmp_date = datetime.utcfromtimestamp(message.date).date()
        now_date = datetime.today().date()
        if tmp_date == now_date:
            force_in_mem_today_actual_for_all()


@app.on_message()
def on_message(client, message):
    chat_id = message.chat.id
    if not message.empty and chat_id in HANDLED_CHATS:
        users = HANDLED_CHATS[chat_id]
        for to in users:
            try:
                if to == chat_id:
                    forwarded_message = message
                else:
                    forwarded_message = message.forward(chat_id=to, as_copy=True)
                chat_name = get_chat_name(message)
                forwarded_message.reply_text('Новое сообщение из "%s"' % chat_name)
            except:
                logging.error('Error when forward to %s' % to)
        force_in_mem_today_actual_for_all()


def main():
    app.start()
    force_in_mem_today_actual_for_all()
    Client.idle()
    app.stop()


if __name__ == '__main__':
    main()
