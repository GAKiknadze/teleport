# -*- coding: utf-8 -*-
import yaml
import re

with open('settings.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)


def __compiler(chats_config: dict) -> dict:
    for ch_k, ch_v in chats_config.items():
        for user_id in ch_v['users'].keys():
            tmp_user = chats_config[ch_k]['users'][user_id]
            for parse_type in ['group', 'item', 'subgroup']:
                if tmp_user.get(parse_type, None):
                    regular_str = tmp_user[parse_type]['regular']
                    regular = re.compile(regular_str, re.M)
                    chats_config[ch_k]['users'][user_id][parse_type]['regular'] = regular
    return chats_config


def __create_handled_chats(chats_config: dict) -> dict:
    tmp_chats = {}
    for i, chat in chats_config.items():
        tmp_chat = {i: [user for user in chat['users'].keys()]}
        tmp_chats.update(tmp_chat)
    return tmp_chats


# telegram
USER_NAME = config['telegram']['user_name']
API_ID = config['telegram']['api']['id']
API_HASH = config['telegram']['api']['hash']

# parser
EXTRA_WORDS = config['parser']['extra']
EXTRA_WORDS = [s.lower() for s in EXTRA_WORDS]

# debug
DEBUG = config['parser']['debug']


# handler
CHATS_CONFIG = __compiler(config['parser']['chats'])

HANDLED_CHATS = __create_handled_chats(CHATS_CONFIG)

# etc
DATE_WITH_TIME_FORMAT = config['etc']['timestamps']['date_time']
DATE_FORMAT = config['etc']['timestamps']['date']
