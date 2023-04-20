import os
import re
import subprocess
import sys

import demoji
import pandas as pd
from telethon import TelegramClient
from telethon.tl import types


def shorten_filename(filename, limit=50):
    filename = filename.replace('\n', ' ')
    """返回合适长度文件名，中间用...显示"""
    if len(filename) <= limit:
        return filename
    else:
        return filename[:int(limit / 2) - 3] + '...' + filename[len(filename) - int(limit / 2):]


def print_all_channel(client: TelegramClient):
    Ids = []
    Names = []
    # Types = []
    for d in client.iter_dialogs():
        if not isinstance(d.entity, types.Channel):
            continue
        Ids.append(d.entity.id)
        Names.append(d.name)
        # Types.append(d.entity)

    df = pd.DataFrame({'ID': Ids, '频道名': Names})
    df.sort_values("频道名", inplace=True)
    df.to_csv('全部频道.csv', index=False)
    print('全部输出完成')


async def getHistoryMessage(client: TelegramClient, chat_id: int, plus_func=None):
    channelData = await client.get_entity(chat_id)
    channel_title = channelData.title
    messages = None
    # Todo 根据plus_func获取指定消息区间
    if plus_func is not None:
        filterFunc = plus_func[:1]
        if filterFunc != 's':
            specifyID = int(plus_func[1:])
            if filterFunc == '=':
                messages = client.iter_messages(chat_id, ids=specifyID)
            elif filterFunc == '>':
                messages = client.iter_messages(chat_id, min_id=specifyID)
            elif filterFunc == '<':
                messages = client.iter_messages(chat_id, max_id=specifyID)
        else:
            tmpId = plus_func[1:].split('s')
            messages = client.iter_messages(chat_id, max_id=int(tmpId[-1]), min_id=int(tmpId[0]))
    else:
        messages = client.iter_messages(chat_id, reverse=True)
    return channel_title, messages


async def GetChatId(client: TelegramClient, chat_id: str) -> int:
    # 检测chat_id是id还是昵称
    isId = re.match(r'-?[1-9][0-9]{4,}', chat_id)
    if isId is None:
        entity = await client.get_entity(chat_id)
        chat_id = entity.id
    else:
        chat_id = int(chat_id)
    return chat_id


def GetFileId(message) -> str:
    _id = 'unknown'
    if hasattr(message.media, 'document'):
        _id = message.media.document.id
    elif hasattr(message.media, 'photo'):
        _id = message.media.photo.id
    return str(_id)


def GetFileName(message, is_photo: bool) -> str:
    # 取名优先级，文件名>描述>ID
    if message.file.name:
        return message.file.name

    if len(message.message) != 0:
        sName = shorten_filename(demoji.replace(message.message, '[emoji]'))
        return re.sub(r'[\\/:*?"<>|]', '_', sName) + message.file.ext

    return GetFileId(message) + message.file.ext


async def print_group(client: TelegramClient, chat_id):
    # 检测chat_id是id还是昵称
    isId = re.match(r'-?[1-9][0-9]{4,}', chat_id)
    if isId is None:
        entity = await client.get_entity(chat_id)
        chat_id = entity.id
    channel_title, messages = await getHistoryMessage(client, int(chat_id))  # messages是倒序的
    channel_title = demoji.replace(channel_title, '[emoji]')
    channel_title = re.sub(r'[\\/:*?"<>|]', '', channel_title)
    links = []
    names = []
    submits = []
    sizes = []
    async for message in messages:
        if message.media is not None:
            # 获取文件类型
            is_photo = isinstance(message.media, types.MessageMediaPhoto)
            is_doc = isinstance(message.media, types.MessageMediaDocument)
            if not (is_photo or is_doc):
                continue

            file_name = GetFileName(message, is_photo)

            file_size = message.file.size
            file_size = f'{round(file_size / 1024 ** 2, 2)}MB' if file_size > 1024 ** 2 else f'{round(file_size / 1024, 2)}KB'
            link = f'https://t.me/c/{chat_id}/{message.id}'
            links.append(link)
            names.append(file_name)
            submits.append(message.message)
            sizes.append(file_size)

    df = pd.DataFrame({'链接': links, '文件名': names, '描述': submits, '大小': sizes})
    # 去重
    df.drop_duplicates(subset=["文件名", "大小"], keep="first", inplace=True)
    df.sort_values("链接", inplace=True, ascending=False)
    df.to_csv(f'{channel_title}-{chat_id}.csv', index=False)
    # df.to_csv(f'{os.environ["save_path"]}/{channel_title}-{chat_id}/{chat_id}.csv', index=False)
    print(chat_id, '全部输出完成')


# 确保数据库没有被占用
def initDb():
    # 获取当前 Python 文件所在的目录路径
    current_dir_path = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录的路径
    root_dir_path = os.path.join(current_dir_path, "..")
    root_abspath = os.path.abspath(root_dir_path)
    if sys.platform == 'linux':
        # 检测的文件路径
        file_path = os.path.join(root_abspath, "python.session")
        # 查询文件占用情况
        p1 = subprocess.Popen(["lsof", file_path], stdout=subprocess.PIPE)
        output, _ = p1.communicate()
        # lsof 命令返回非零值表示文件被占用
        if p1.returncode == 0:
            print("数据库文件被占用，释放中")
            # kill 命令终止占用文件的进程
            p2 = subprocess.Popen(["kill", "$(lsof -t " + file_path + ")"])
            p2.wait()
    else:
        return


async def Hook(client: TelegramClient):
    # 打开文本文件并读取所有行
    # with open('./unique_data.txt', 'r') as f:
    #     lines = f.readlines()
    # peo = await client.get_entity('mihayoudt_bot')
    # i = 0
    # for line in lines:
    #     i += 1
    #     print('\r', f'正在查询{line.strip()},进度{i}/{len(lines)}', end='', flush=True)
    #     await client.send_message(peo, line.strip())
    #     time.sleep(70)
    pass
