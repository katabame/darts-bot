from hata import Activity, ActivityType, Emoji, BUILTIN_EMOJIS, Client, Embed, now_as_id, wait_for_interruption

from random import choice, choices
from string import ascii_letters, digits
import json
import re

import constants
import utils

import count_up
import standard_cricket
import zero_one

## Config
with open('config.json', 'r') as f:
    config = json.load(f)

## Client
Satori = Client(
    config['token'],
    extensions = 'slash',
    activity = Activity('ダーツ', activity_type = ActivityType.competing)
)

@Satori.interactions(guild = config['guildId'], show_for_invoking_user_only = True)
async def start(
    event,
    game: (constants.games, 'どのゲームを開始しますか？'),
    player1: ('user', 'プレイヤー1を指定してください') = None,
    player2: ('user', 'プレイヤー2を指定してください') = None,
    cointoss: ('bool', 'コイントスを行いますか？') = False
):
    yield
    red, blue = utils.determine_teams(event.user, player1, player2, cointoss)
    embed = utils.create_game_embed(game, red, blue)
    channel = await Satori.channel_create(
        event.guild_id,
        parent_id = event.channel.parent_id,
        name = f'darts-{"".join(choices(ascii_letters + digits, k = 5))}'
    )
    await Satori.message_create(channel, utils.create_start_message(red, blue))
    await Satori.message_create(channel, embed = embed)
    yield f'専用チャンネル #{channel.name} を作成しました！ HAVE A NICE DARTS!'

@Satori.interactions(guild = config['guildId'], show_for_invoking_user_only = True)
async def delete_channel(
    event,
    channel: ('channel', '削除するチャンネルを選択してください') = None
):
    yield
    target_channel = event.channel if channel is None else channel
    if re.fullmatch(r'^darts\-[a-zA-Z0-9]{5}$', target_channel.name):
        await Satori.channel_delete(target_channel)
        if event.channel != target_channel:
            yield f'#{target_channel.name} を削除しました'
    else:
        yield f'#{target_channel.name} は削除対象チャンネルではありません'

@Satori.interactions(guild = config['guildId'])
async def cointoss(
    event,
    head: ('str', '表の選択肢を入力してください'),
    tail: ('str', '裏の選択肢を入力してください')
):
    return choice([head, tail])

@Satori.events
async def message_create(client, message):
    if re.fullmatch(r'^darts\-[a-zA-Z0-9]{5}$', message.channel.name) == None:
        return
    previous_messages = await client.message_get_chunk(message.channel, before = message.id, limit = 1)
    previous_message = previous_messages[0]

    embed = previous_message.embed.copy()
    if previous_message.author.id == client.id: #and message.content.contains('OVER!') == False:
        #with client.keep_typing(message.channel):
        await client.reaction_clear(previous_message)
        await client.message_delete(message)
        scores = re.findall(r'(|S|D|T)(20|1[0-9]|[1-9]|BULL|OUT)', message.content.upper().replace('-', ''))
        if len(scores) != 3:
            await client.reaction_add(previous_message, BUILTIN_EMOJIS['warning'])
            return
        else:
            if embed.author.name.startswith('COUNT-UP'):
                new_embed, is_gameover = count_up.create_embed(embed, scores)
            elif embed.author.name == 'STANDARD CRICKET':
                new_embed, is_gameover = standard_cricket.create_embed(embed, scores)
            else:
                new_embed, is_gameover = zero_one.create_embed(embed, scores)

        if is_gameover:
            new_embed.fields[0].value = new_embed.fields[0].value.replace('REALTIME', 'ESTABLISHED')
            new_embed.fields[0].name = new_embed.fields[0].name.replace('🎯 ', '')
            if len(embed.fields) == 2:
                new_embed.fields[1].value = new_embed.fields[1].value.replace('REALTIME', 'ESTABLISHED')
                new_embed.fields[1].name = new_embed.fields[1].name.replace('🎯 ', '')
            await client.message_create(message.channel, 'GAME OVER!')
        
        await client.message_edit(previous_message, embed = new_embed)

## Start
@Satori.events
async def ready(client):
    print(f'Logged in as {client:f} ({client.id})')
if __name__ == '__main__':
    Satori.start()
    wait_for_interruption()
