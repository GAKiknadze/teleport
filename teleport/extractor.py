# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime
from os import walk, makedirs, remove, path
from shutil import rmtree

import demoji
import flag
from xlrd import open_workbook
from xlwt import Workbook

from settings import CHATS_CONFIG
import re

if not demoji.last_downloaded_timestamp():
    demoji.download_codes()


def get_today_extract_container_path():
    return 'extracted/%s' % datetime.today().date()


def get_today_extract_path(filename: str):
    return '%s/%s' % (get_today_extract_container_path(), filename)


def apply_emoji_filter(text: str) -> str:
    emoji_in_message = demoji.findall(text)
    for emoji in emoji_in_message.items():
        emoji_code = emoji[0]
        emoji_description = emoji[1]
        if "flag" in emoji_description:
            try:
                country = flag.dflagize(emoji_code)
                text = text.replace(emoji_code, country)
            except Exception as e:
                logging.exception(e)
                text = text.replace(emoji_code, '')
        else:
            text = text.replace(emoji_code, '')
    text = text.replace("️", "")
    return text


def extract_from_file(filepath: str) -> list:
    result = []
    workbook = open_workbook(filepath)
    sheet = workbook.sheet_by_index(0)
    for row_index in range(sheet.nrows):
        title_cell = sheet.cell(row_index, 0)
        price_cell = sheet.cell(row_index, 1)
        result.append([title_cell.value, price_cell.value])
    return result


def extract_from_text(text: str, chat_id: int, user_id: int) -> list:

    msg_config = dict(CHATS_CONFIG[chat_id]['users'][user_id])

    def create_dict(obj: tuple, params: dict) -> dict:
        res = {}
        for index, value in params.items():
            new_value = obj[index]
            if value == 'pr':
                new_value = new_value.replace(',', '.').replace(' ', '')
            res.update({value: new_value})
        return res

    def get_list(obj: dict) -> list:
        res = ''
        for i in ['br', 'sr', 'md', 'cn']:
            ans = obj.get(i, None)
            if ans:
                res += ' ' + ans
        res = res.replace('   ', ' ')
        res = res.replace('  ', ' ')
        return [res, obj.get('pr', '0')]

    def get_group(text: str, ftype: str, config: dict) -> list:
        res = []
        regular = config[ftype]['regular']
        params = config[ftype]['params']
        while True:
            ans = regular.search(text)
            if not ans:
                break
            group_dict = create_dict(regular.findall(text)[0], params)
            ended = ans.span(0)[1]
            new_dict = dict(config)
            new_dict.pop(ftype)
            for child in search(text[:ended], new_dict):
                child.update(group_dict)
                res.append(child)
            text = text[ended:]
        return res

    def search(text: str, msg_config: dict) -> list:
        keys = msg_config.keys()
        if 'group' in keys:
            res = get_group(text, 'group', msg_config)
        elif 'subgroup' in msg_config.keys():
            res = get_group(text, 'subgroup', msg_config)
        else:
            regular = msg_config['item']['regular']
            params = msg_config['item']['params']
            ans = regular.findall(text)
            res = []
            if ans:
                for i in ans:
                    res.append(create_dict(i, params))
        return res

    return [get_list(i) for i in search(text, msg_config)]


def extract_to_xls_file(extract: list, filename: str):
    workbook = Workbook()
    sheet = workbook.add_sheet("Таблица 1")
    for row_index in range(len(extract)):
        row_data = extract[row_index]
        sheet.write(row_index, 0, row_data[0])
        sheet.write(row_index, 1, row_data[1])
    try:
        makedirs(filename)
    except IOError as error:
        logging.exception(error)
    workbook.save('%s.xls' % filename)


def extract_to_today_xls_file(extract: list, filename: str):
    return extract_to_xls_file(extract, get_today_extract_path(filename))


def __fix__get_today_extract_fullpaths_by_filename(filename: str) -> list:
    result = []
    fullname = '%s.xls' % filename
    for (root, _, filenames) in walk(get_today_extract_container_path()):
        for filename0 in filenames:
            if filename0 == fullname:
                result.append(path.join(root, filename0))
    logging.info("__fix__get_today_extract_fullpaths_by_filename=[%s]" % ','.join(result))
    return result


def __dirty__delete_extract_xls_file(a: str):
    for file in __fix__get_today_extract_fullpaths_by_filename(a):
        remove(file)


def delete_extract_container_folder(a: str):
    try:
        dir_to_rm = get_today_extract_path(a)
        logging.info('delete_extract_container_folder(%s)' % dir_to_rm)
        rmtree(dir_to_rm, ignore_errors=True)
    except Exception:
        pass


def create_today_actual_xls(filepath: str):
    xml_files = []
    today_extract_path = get_today_extract_path(filepath)

    # need to modify for support tree files
    for (root, _, filenames) in walk(today_extract_path):
        xml_files.extend(filenames)
        break

    extracts = []
    for xml_file in xml_files:
        file_path = '%s/%s' % (today_extract_path, xml_file)
        extracts.extend(extract_from_file(file_path))

    save_today_actual_xls(extracts, filepath)


def save_today_actual_xls(today_extract: list, filepath: str):
    extract_to_xls_file(today_extract, 'public/%s/actual' % filepath)
