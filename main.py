from hata import Activity, ActivityType, Emoji, BUILTIN_EMOJIS, Client, Embed, now_as_id, wait_for_interruption

from random import choice, choices
from string import ascii_letters, digits
import json
import re

import constants

## Config
with open('config.json', 'r') as f:
    config = json.load(f)

## Client
Satori = Client(
    config['token'],
    extensions = 'slash',
    activity = Activity('ダーツ', activity_type = ActivityType.competing)
)

## Slash commands
@Satori.interactions(guild = config['guildId'], show_for_invoking_user_only = True)
async def start(
    event,
    game: (
        {
            '301': '301',
            '501': '501',
            '701': '701',
            #'901': '901',
            #'1101': '1101',
            #'1501': '1501',
            'CRICKET': 'cricket',
            'COUNT-UP': 'count-up'
        },
        'どのゲームを開始しますか？'
    ),
    player1: ('user', 'プレイヤー1を指定してください') = None,
    player2: ('user', 'プレイヤー2を指定してください') = None,
    cointoss: ('bool', 'コイントスを行いますか？') = False
):
    yield

    message = ''
    embed = Embed()
    embed.add_author(game.upper())

    # Flags
    red = None
    blue = None

    # Determine Red side and Blue side
    if player1 == None and player2 == None:
        red = event.user
    elif player1 != None and player2 == None:
        red = player1
    elif player1 == None and player2 != None:
        red = player2
    else:
        if cointoss == True:
            players = [player1, player2]
            red = choice(players)
            players.remove(red)
            blue = players[0]
        else:
            red = player1
            blue = player2
    if blue == None:
        embed.title = f'{red.display_name}'
        message += f'<@{red.id}> GAME ON!'
    else:
        embed.title = f'{red.display_name} vs {blue.display_name}'
        message += f'<@{red.id}> vs <@{blue.id}> GAME ON!'

    if game == 'cricket':
        embed.color = 0x3030ff
        embed.add_field(
            name = f'🎯 {red.display_name} [0] (Total: 0 marks)',
            value = constants.stats_cricket,
            inline = True
        )
        embed.description = constants.marks_red_only

        if blue != None:
            embed.add_field(
                name = f'{blue.display_name} [0] (Total: 0 marks)',
                value= constants.stats_cricket,
                inline = True
            )
            embed.description = constants.marks

    elif game == 'count-up':
        embed.color = 0x30ff30
        embed.add_field(
            name = f'🎯 {red.display_name} [0]',
            value = constants.stats_countup,
            inline = True
        )
        if blue != None:
            embed.add_field(
                name = f'{blue.display_name} [0]',
                value= constants.stats_countup,
                inline = True
            )

    else:
        embed.color = 0xff3030
        embed.add_field(
            name = f'🎯 {red.display_name} [{game}]',
            value = constants.stats_01,
            inline = True
        )
        if blue != None:
            embed.add_field(
                name = f'{blue.display_name} [{game}]',
                value= constants.stats_01,
                inline = True
            )

    channel_id = ''.join(choices(ascii_letters+digits, k = 5))
    channel = await Satori.channel_create(
        event.guild_id,
        parent_id = event.channel.parent_id,
        name = f'darts-{channel_id}'
    )

    await Satori.message_create(channel, message)
    await Satori.message_create(channel, embed = embed)
    yield f'専用チャンネル #{channel.name} を作成しました！ HAVE A NICE DARTS!'

@Satori.interactions(guild = config['guildId'], show_for_invoking_user_only = True)
async def delete_channel(
    event,
    channel: ('channel', '削除するチャンネルを選択してください') = None
):
    yield
    target_channel = event.channel
    if channel != None:
        target_channel = channel

    if re.fullmatch(r'^darts\-[a-zA-Z0-9]{5}$', target_channel.name):
        await Satori.channel_delete(target_channel)
        yield f'#{target_channel.name} を削除しました'
    else:
        yield f'#{target_channel.name} は削除対象チャンネルではありません'

## Events
@Satori.events
async def message_create(client, message):
    previous_messages = await client.message_get_chunk(message.channel, before = message.id, limit = 1)
    previous_message = previous_messages[0]
    gameover_flag = False

    if previous_message.author.id == client.id and message.content != 'GAME OVER!':
        await client.reaction_clear(previous_message)
        scores = re.findall(r'(|S|D|T)(20|1[0-9]|[1-9]|BULL|OUT)', message.content.upper().replace('-', ''))
        round_score = 0
        round_score_text = ''
        if len(scores) == 3:
            for score in scores:
                if score[1] == 'BULL':
                    round_score += 50
                    if score[0] == 'D':
                        round_score_text += f'D-BULL '
                    else:
                        round_score_text += f'BULL '
                elif score[1] == 'OUT':
                    round_score += 0
                    round_score_text += 'OUT '
                elif score[0] == '' or score[0] == 'S':
                    round_score += int(score[1])
                    round_score_text += f'{score[1]} '
                elif score[0] == 'D':
                    round_score += (int(score[1]) * 2)
                    round_score_text += f'D{score[1]} '
                elif score[0] == 'T':
                    round_score += (int(score[1]) * 3)
                    round_score_text += f'T{score[1]} '
        else:
            await client.message_delete(message)
            await client.reaction_add(previous_message, BUILTIN_EMOJIS['warning'])
            return

        embed = previous_message.embed.copy()

        if len(embed.fields) == 2:
            if embed.author.name == 'COUNT-UP':
                # red thrown
                if embed.fields[0].name.startswith('🎯'):
                    field_name = embed.fields[0].name.split()
                    player_name = field_name[1]
                    current_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score += round_score
                    embed.fields[0].name = f'{player_name} [{current_score}]'
                    embed.fields[1].name = f'🎯 {embed.fields[1].name}'

                    field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                    current_round = 1
                    new_field_value = ''

                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                    for i in range(current_round + 1, 9):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if current_round == 8:
                        new_field_value += 'Stats [ESTABLISHED]\n'
                        new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'
                    else:
                        new_field_value += 'Stats [REALTIME]\n'
                        new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

                    embed.fields[0].value = new_field_value

                # blue thrown
                else:
                    field_name = embed.fields[1].name.split()
                    player_name = field_name[1]
                    current_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score += round_score
                    embed.fields[1].name = f'{player_name} [{current_score}]'
                    embed.fields[0].name = f'🎯 {embed.fields[0].name}'

                    field_value = re.findall(r'^.+$', embed.fields[1].value, re.MULTILINE)
                    current_round = 1
                    new_field_value = ''

                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                    for i in range(current_round + 1, 9):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if current_round == 8:
                        new_field_value += 'Stats [ESTABLISHED]\n'
                        new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

                        embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                        gameover_flag = True
                    else:
                        new_field_value += 'Stats [REALTIME]\n'
                        new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

                    embed.fields[1].value = new_field_value

            elif embed.author.name == 'CRICKET':
                # red thrown
                if embed.fields[0].name.startswith('🎯'):
                    round_score = 0
                    round_marks = 0
                    round_marks_text = ''
                    marks_red = [] # 20:0, 19:1, 18:2, 17:3, 16:4, 15:5, BULL:6
                    marks_blue = []
                    marks_text = ''
                    current_round = 1
                    full_open_flag = True
                    ignore_darts = 0

                    target_marks = re.findall(r'^.+$', embed.description, re.MULTILINE)
                    for target_mark in target_marks:
                        mark_red = re.findall(r'.*([0-3])mark_red.*', target_mark)
                        marks_red.append(int(mark_red[0]))
                        mark_blue = re.findall(r'.*([0-3])mark_blue.*', target_mark)
                        marks_blue.append(int(mark_blue[0]))

                    for i in range(0, 7):
                        if marks_red[i] != 3:
                            full_open_flag = False

                    for score in scores:
                        if score[1] == 'BULL':
                            if score[0] == 'D':
                                if marks_blue[6] == 3:
                                    if marks_red[6] == 3:
                                        round_marks_text += f'{constants.mark_0_red}'
                                    elif marks_red[6] == 2:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_red}'
                                        marks_red[6] += 1
                                    else:
                                        round_marks += 2
                                        round_marks_text += f'{constants.mark_2_red}'
                                        marks_red[6] += 2
                                else:
                                    round_marks += 2
                                    round_marks_text += f'{constants.mark_2_red}'
                                    if marks_red[6] == 3:
                                        round_score += 50
                                    elif marks_red[6] == 2:
                                        marks_red[6] += 1
                                        round_score += 25
                                    else:
                                        marks_red[6] += 2
                            else:
                                if marks_blue[6] == 3:
                                    if marks_red[6] == 3:
                                        round_marks_text += f'{constants.mark_0_red}'
                                    else:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_red}'
                                        marks_red[6] += 1
                                else:
                                    round_marks += 1
                                    round_marks_text += f'{constants.mark_1_red}'
                                    if marks_red[6] == 3:
                                        round_score += 25
                                    else:
                                        marks_red[6] += 1

                        elif score[1] == 'OUT':
                            round_marks += 0
                            round_marks_text += f'{constants.mark_0_red}'

                            if full_open_flag == True:
                                ignore_darts += 1

                        elif score[0] == '' or score[0] == 'S':
                            if int(score[1]) >= 15:
                                if marks_blue[20 - int(score[1])] == 3:
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_red}'
                                    else:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_red}'
                                        marks_red[20 - int(score[1])] += 1
                                else:
                                    round_marks += 1
                                    round_marks_text += f'{constants.mark_1_red}'
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_score += int(score[1])
                                    else:
                                        marks_red[20 - int(score[1])] += 1
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_red}'

                        elif score[0] == 'D':
                            if int(score[1]) >= 15:
                                if marks_blue[20 - int(score[1])] == 3:
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_red}'
                                    if marks_red[20 - int(score[1])] == 2:
                                        round_marks_text += f'{constants.mark_1_red}'
                                        round_marks += 1
                                        marks_red[20 - int(score[1])] += 1
                                    else:
                                        round_marks_text += f'{constants.mark_2_red}'
                                        round_marks += 2
                                        marks_red[20 - int(score[1])] += 2
                                else:
                                    round_marks += 2
                                    round_marks_text += f'{constants.mark_2_red}'
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_score += int(score[1]) * 2
                                    elif marks_red[20 - int(score[1])] == 2:
                                        marks_red[20 - int(score[1])] += 1
                                        round_score += int(score[1])
                                    else:
                                        marks_red[20 - int(score[1])] += 2
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_red}'

                        elif score[0] == 'T':
                            if int(score[1]) >= 15:
                                if marks_blue[20 - int(score[1])] == 3:
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_red}'
                                    elif marks_red[20 - int(score[1])] == 2:
                                        round_marks_text += f'{constants.mark_1_red}'
                                        round_marks += 1
                                        marks_red[20 - int(score[1])] += 1
                                    elif marks_red[20 - int(score[1])] == 1:
                                        round_marks_text += f'{constants.mark_2_red}'
                                        round_marks += 2
                                        marks_red[20 - int(score[1])] += 2
                                    else:
                                        round_marks_text += f'{constants.mark_3_red}'
                                        round_marks += 3
                                        marks_red[20 - int(score[1])] += 3
                                else:
                                    round_marks += 3
                                    round_marks_text += f'{constants.mark_3_red}'
                                    if marks_red[20 - int(score[1])] == 3:
                                        round_score += int(score[1]) * 3
                                    elif marks_red[20 - int(score[1])] == 2:
                                        marks_red[20 - int(score[1])] += 1
                                        round_score += int(score[1]) * 2
                                    elif marks_red[20 - int(score[1])] == 1:
                                        marks_red[20 - int(score[1])] += 2
                                        round_score += int(score[1])
                                    else:
                                        marks_red[20 - int(score[1])] += 3
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_red}'

                    for i in range(0, 7):
                        if i == 6:
                            if marks_red[i] == 3:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_3_red} ~~**BULL**~~ {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_0_blue}\n'

                            elif marks_red[i] == 2:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_0_blue}\n'

                            elif marks_red[i] == 1:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_0_blue}\n'

                            else:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_0_blue}\n'
                        else:
                            if marks_red[i] == 3:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_3_red} ~~**{20 - i}**~~ {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_0_blue}\n'

                            elif marks_red[i] == 2:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_0_blue}\n'

                            elif marks_red[i] == 1:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_0_blue}\n'

                            else:
                                if marks_blue[i] == 3:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_3_blue}\n'
                                elif marks_blue[i] == 2:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_blue[i] == 1:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_0_blue}\n'

                    embed.description = marks_text

                    field_name = embed.fields[0].name.split()
                    player_name = field_name[1]
                    current_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score += round_score
                    current_marks = int(field_name[4])
                    current_marks += round_marks
                    embed.fields[0].name = f'{player_name} [{current_score}] (Total: {current_marks} marks)'
                    embed.fields[1].name = f'🎯 {embed.fields[1].name}'

                    field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                    new_field_value = ''
                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                new_field_value += f'**R{round_data[0]}** {round_marks_text} [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                    for i in range(current_round + 1, 16):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if current_round == 15:
                        new_field_value += 'Stats [ESTABLISHED]\n'
                        new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'
                    else:
                        new_field_value += 'Stats [REALTIME]\n'
                        new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'

                    if full_open_flag == True:
                        embed.fields[1].name = embed.fields[1].name.replace('🎯 ', '')
                        gameover_flag = True

                    embed.fields[0].value = new_field_value

                # blue thrown
                else:
                    round_score = 0
                    round_marks = 0
                    round_marks_text = ''
                    marks_red = [] # 20:0, 19:1, 18:2, 17:3, 16:4, 15:5, BULL:6
                    marks_blue = []
                    marks_text = ''
                    current_round = 1
                    full_open_flag = True
                    ignore_darts = 0

                    target_marks = re.findall(r'^.+$', embed.description, re.MULTILINE)
                    for target_mark in target_marks:
                        mark_red = re.findall(r'.*([0-3])mark_red.*', target_mark)
                        marks_red.append(int(mark_red[0]))
                        mark_blue = re.findall(r'.*([0-3])mark_blue.*', target_mark)
                        marks_blue.append(int(mark_blue[0]))

                    for i in range(0, 7):
                        if marks_blue[i] != 3:
                            full_open_flag = False

                    for score in scores:
                        if score[1] == 'BULL':
                            if score[0] == 'D':
                                if marks_red[6] == 3:
                                    if marks_blue[6] == 3:
                                        round_marks_text += f'{constants.mark_0_blue}'
                                    elif marks_blue[6] == 2:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_blue}'
                                        marks_blue[6] += 1
                                    else:
                                        round_marks += 2
                                        round_marks_text += f'{constants.mark_2_blue}'
                                        marks_blue[6] += 2
                                else:
                                    round_marks += 2
                                    round_marks_text += f'{constants.mark_2_blue}'
                                    if marks_blue[6] == 3:
                                        round_score += 50
                                    elif marks_blue[6] == 2:
                                        marks_blue[6] += 1
                                        round_score += 25
                                    else:
                                        marks_blue[6] += 2
                            else:
                                if marks_red[6] == 3:
                                    if marks_blue[6] == 3:
                                        round_marks_text += f'{constants.mark_0_blue}'
                                    else:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_blue}'
                                        marks_blue[6] += 1
                                else:
                                    round_marks += 1
                                    round_marks_text += f'{constants.mark_1_blue}'
                                    if marks_blue[6] == 3:
                                        round_score += 25
                                    else:
                                        marks_blue[6] += 1

                        elif score[1] == 'OUT':
                            round_marks += 0
                            round_marks_text += f'{constants.mark_0_blue}'

                            if full_open_flag == True:
                                ignore_darts += 1

                        elif score[0] == '' or score[0] == 'S':
                            if int(score[1]) >= 15:
                                if marks_red[20 - int(score[1])] == 3:
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_blue}'
                                    else:
                                        round_marks += 1
                                        round_marks_text += f'{constants.mark_1_blue}'
                                        marks_blue[20 - int(score[1])] += 1
                                else:
                                    round_marks += 1
                                    round_marks_text += f'{constants.mark_1_blue}'
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_score += int(score[1])
                                    else:
                                        marks_blue[20 - int(score[1])] += 1
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_blue}'

                        elif score[0] == 'D':
                            if int(score[1]) >= 15:
                                if marks_red[20 - int(score[1])] == 3:
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_blue}'
                                    if marks_blue[20 - int(score[1])] == 2:
                                        round_marks_text += f'{constants.mark_1_blue}'
                                        round_marks += 1
                                        marks_blue[20 - int(score[1])] += 1
                                    else:
                                        round_marks_text += f'{constants.mark_2_blue}'
                                        round_marks += 2
                                        marks_blue[20 - int(score[1])] += 2
                                else:
                                    round_marks += 2
                                    round_marks_text += f'{constants.mark_2_blue}'
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_score += int(score[1]) * 2
                                    elif marks_blue[20 - int(score[1])] == 2:
                                        marks_blue[20 - int(score[1])] += 1
                                        round_score += int(score[1])
                                    else:
                                        marks_blue[20 - int(score[1])] += 2
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_blue}'

                        elif score[0] == 'T':
                            if int(score[1]) >= 15:
                                if marks_red[20 - int(score[1])] == 3:
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_marks_text += f'{constants.mark_0_blue}'
                                    elif marks_blue[20 - int(score[1])] == 2:
                                        round_marks_text += f'{constants.mark_1_blue}'
                                        round_marks += 1
                                        marks_blue[20 - int(score[1])] += 1
                                    elif marks_blue[20 - int(score[1])] == 1:
                                        round_marks_text += f'{constants.mark_2_blue}'
                                        round_marks += 2
                                        marks_blue[20 - int(score[1])] += 2
                                    else:
                                        round_marks_text += f'{constants.mark_3_blue}'
                                        round_marks += 3
                                        marks_blue[20 - int(score[1])] += 3
                                else:
                                    round_marks += 3
                                    round_marks_text += f'{constants.mark_3_blue}'
                                    if marks_blue[20 - int(score[1])] == 3:
                                        round_score += int(score[1]) * 3
                                    elif marks_blue[20 - int(score[1])] == 2:
                                        marks_blue[20 - int(score[1])] += 1
                                        round_score += int(score[1]) * 2
                                    elif marks_blue[20 - int(score[1])] == 1:
                                        marks_blue[20 - int(score[1])] += 2
                                        round_score += int(score[1])
                                    else:
                                        marks_blue[20 - int(score[1])] += 3
                            else:
                                round_marks += 0
                                round_marks_text += f'{constants.mark_0_blue}'

                    for i in range(0, 7):
                        if i == 6:
                            if marks_blue[i] == 3:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} ~~**BULL**~~ {constants.mark_3_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_3_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_3_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_3_blue}\n'

                            elif marks_blue[i] == 2:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_2_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_2_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_2_blue}\n'

                            elif marks_blue[i] == 1:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_1_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_1_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_1_blue}\n'

                            else:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **BULL** {constants.mark_0_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **BULL** {constants.mark_0_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **BULL** {constants.mark_0_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **BULL** {constants.mark_0_blue}\n'
                        else:
                            if marks_blue[i] == 3:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} ~~**{20 - i}**~~ {constants.mark_3_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_3_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_3_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_3_blue}\n'

                            elif marks_blue[i] == 2:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_2_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_2_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_2_blue}\n'

                            elif marks_blue[i] == 1:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_1_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_1_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_1_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_1_blue}\n'

                            else:
                                if marks_red[i] == 3:
                                    marks_text += f'{constants.mark_3_red} **{20 - i}** {constants.mark_0_blue}\n'
                                elif marks_red[i] == 2:
                                    marks_text += f'{constants.mark_2_red} **{20 - i}** {constants.mark_0_blue}\n'
                                elif marks_red[i] == 1:
                                    marks_text += f'{constants.mark_1_red} **{20 - i}** {constants.mark_0_blue}\n'
                                else:
                                    marks_text += f'{constants.mark_0_red} **{20 - i}** {constants.mark_0_blue}\n'

                    embed.description = marks_text

                    field_name = embed.fields[1].name.split()
                    player_name = field_name[1]
                    current_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score += round_score
                    current_marks = int(field_name[4])
                    current_marks += round_marks
                    embed.fields[1].name = f'{player_name} [{current_score}] (Total: {current_marks} marks)'
                    embed.fields[0].name = f'🎯 {embed.fields[0].name}'

                    field_value = re.findall(r'^.+$', embed.fields[1].value, re.MULTILINE)
                    new_field_value = ''
                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                new_field_value += f'**R{round_data[0]}** {round_marks_text} [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                    for i in range(current_round + 1, 16):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if current_round == 15 or full_open_flag == True:
                        new_field_value += 'Stats [ESTABLISHED]\n'
                        new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'
                        embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                        gameover_flag = True
                    else:
                        new_field_value += 'Stats [REALTIME]\n'
                        new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'

                    embed.fields[1].value = new_field_value

            else:
                # red thrown
                if embed.fields[0].name.startswith('🎯'):
                    embed.fields[1].name = f'🎯 {embed.fields[1].name}'
                    target_score = int(embed.author.name)
                    field_name = embed.fields[0].name.split()
                    player_name = field_name[1]
                    previous_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score = previous_score - round_score
                    bust_flag = False
                    ignore_darts = 0

                    if current_score < 0:
                        bust_flag = True

                    if current_score == 0:
                        ignore_darts = len(re.findall(r'(OUT)', round_score_text))

                    if bust_flag == False:
                        embed.fields[0].name = f'{player_name} [{current_score}]'
                    else:
                        embed.fields[0].name = f'{player_name} [{previous_score}]'

                    field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                    current_round = 1
                    new_field_value = ''
                    stats = []
                    stats_established_flag = False

                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                if bust_flag == True:
                                    new_field_value += f'**R{round_data[0]}** [BUST] {round_score_text}\n'
                                else:
                                    new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                        established = re.findall(r'80% \(12R\) Stats \[(REALTIME|ESTABLISHED)\]', value)
                        if len(established) != 0 and established[0] == 'ESTABLISHED':
                            stats_established_flag = True

                        if value.startswith('**PP'):
                            stats.append(value)

                    for i in range(current_round + 1, 16):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if int(target_score * 0.2) > current_score:
                        new_field_value += '80% Stats [ESTABLISHED]\n'
                        if stats_established_flag == True:
                            new_field_value += f'{stats[0]}\n'
                        else:
                            if bust_flag == True:
                                new_field_value += f'{stats[0]}\n'
                            else:
                                new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                    else:
                        if current_score == 0:
                            new_field_value += '80% Stats [ESTABLISHED]\n'
                        else:
                            new_field_value += '80% Stats [REALTIME]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[0]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                    new_field_value += '\n'

                    if current_round == 15 or current_score == 0:
                        new_field_value += '100% Stats [ESTABLISHED]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[1]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                    else:
                        if current_score == 0:
                            new_field_value += '100% Stats [ESTABLISHED]\n'
                        else:
                            new_field_value += '100% Stats [REALTIME]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[1]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                    if current_score == 0:
                        embed.fields[1].name = embed.fields[1].name.replace('🎯 ', '')
                        gameover_flag = True

                    embed.fields[0].value = new_field_value
                
                # blue thrown
                else:
                    embed.fields[0].name = f'🎯 {embed.fields[0].name}'
                    target_score = int(embed.author.name)
                    field_name = embed.fields[1].name.split()
                    player_name = field_name[1]
                    previous_score = int(field_name[2].replace('[', '').replace(']', ''))
                    current_score = previous_score - round_score
                    bust_flag = False
                    ignore_darts = 0

                    if current_score < 0:
                        bust_flag = True

                    if current_score == 0:
                        ignore_darts = len(re.findall(r'(OUT)', round_score_text))

                    if bust_flag == False:
                        embed.fields[1].name = f'{player_name} [{current_score}]'
                    else:
                        embed.fields[1].name = f'{player_name} [{previous_score}]'

                    field_value = re.findall(r'^.+$', embed.fields[1].value, re.MULTILINE)
                    current_round = 1
                    new_field_value = ''
                    stats = []
                    stats_established_flag = False

                    score_added_flag = False
                    for value in field_value:
                        round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                        for round_data in round_parsed_data:
                            if round_data[1] != '':
                                new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                            elif score_added_flag == False:
                                current_round = int(round_data[0])
                                if bust_flag == True:
                                    new_field_value += f'**R{round_data[0]}** [BUST] {round_score_text}\n'
                                else:
                                    new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                                score_added_flag = True

                        established = re.findall(r'80% \(12R\) Stats \[(REALTIME|ESTABLISHED)\]', value)
                        if len(established) != 0 and established[0] == 'ESTABLISHED':
                            stats_established_flag = True

                        if value.startswith('**PP'):
                            stats.append(value)

                    for i in range(current_round + 1, 16):
                        new_field_value += f'**R{i:02}**\n'

                    new_field_value += '\n'

                    if int(target_score * 0.2) > current_score:
                        new_field_value += '80% Stats [ESTABLISHED]\n'
                        if stats_established_flag == True:
                            new_field_value += f'{stats[0]}\n'
                        else:
                            if bust_flag == True:
                                new_field_value += f'{stats[0]}\n'
                            else:
                                new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                    else:
                        if current_score == 0:
                            new_field_value += '80% Stats [ESTABLISHED]\n'
                        else:
                            new_field_value += '80% Stats [REALTIME]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[0]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                    new_field_value += '\n'

                    if current_round == 15 or current_score == 0:
                        new_field_value += '100% Stats [ESTABLISHED]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[1]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                    else:
                        if current_score == 0:
                            new_field_value += '100% Stats [ESTABLISHED]\n'
                        else:
                            new_field_value += '100% Stats [REALTIME]\n'

                        if bust_flag == True:
                            new_field_value += f'{stats[1]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                    if current_score == 0:
                        embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                        gameover_flag = True

                    embed.fields[1].value = new_field_value

        else:
            # solo mode
            if embed.author.name == 'COUNT-UP':
                field_name = embed.fields[0].name.split()
                player_name = field_name[1]
                current_score = int(field_name[2].replace('[', '').replace(']', ''))
                current_score += round_score
                embed.fields[0].name = f'🎯 {player_name} [{current_score}]'

                field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                current_round = 1
                new_field_value = ''

                score_added_flag = False
                for value in field_value:
                    round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                    for round_data in round_parsed_data:
                        if round_data[1] != '':
                            new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                        elif score_added_flag == False:
                            current_round = int(round_data[0])
                            new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                            score_added_flag = True

                for i in range(current_round + 1, 9):
                    new_field_value += f'**R{i:02}**\n'

                new_field_value += '\n'

                if current_round == 8:
                    new_field_value += 'Stats [ESTABLISHED]\n'
                    new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

                    embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                    gameover_flag = True
                else:
                    new_field_value += 'Stats [REALTIME]\n'
                    new_field_value += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

                embed.fields[0].value = new_field_value

            elif embed.author.name == 'CRICKET':
                round_score = 0
                round_marks = 0
                round_marks_text = ''
                marks_red = [] # 20:0, 19:1, 18:2, 17:3, 16:4, 15:5, BULL:6
                marks_red_text = ''
                current_round = 1
                full_open_flag = True
                ignore_darts = 0

                target_marks = re.findall(r'^.+$', embed.description, re.MULTILINE)
                for target_mark in target_marks:
                    mark = re.findall(r'.*([0-3])mark_red.*', target_mark)
                    marks_red.append(int(mark[0]))

                for i in range(0, 7):
                    if marks_red[i] != 3:
                        full_open_flag = False

                    if i == 6:
                        if marks_red[i] == 3:
                            marks_red_text += f'{constants.mark_3_red} **BULL**\n'
                        elif marks_red[i] == 2:
                            marks_red_text += f'{constants.mark_2_red} **BULL**\n'
                        elif marks_red[i] == 1:
                            marks_red_text += f'{constants.mark_1_red} **BULL**\n'
                        else:
                            marks_red_text += f'{constants.mark_0_red} **BULL**\n'
                    else:
                        if marks_red[i] == 3:
                            marks_red_text += f'{constants.mark_3_red} **{20 - i}**\n'
                        elif marks_red[i] == 2:
                            marks_red_text += f'{constants.mark_2_red} **{20 - i}**\n'
                        elif marks_red[i] == 1:
                            marks_red_text += f'{constants.mark_1_red} **{20 - i}**\n'
                        else:
                            marks_red_text += f'{constants.mark_0_red} **{20 - i}**\n'

                for score in scores:
                    if score[1] == 'BULL':
                        if score[0] == 'D':
                            round_marks += 2
                            round_marks_text += f'{constants.mark_2_red}'
                            if marks_red[6] == 3:
                                round_score += 50
                            elif marks_red[6] == 2:
                                marks_red[6] += 1
                                round_score += 25
                            else:
                                marks_red[6] += 2
                        else:
                            round_marks += 1
                            round_marks_text += f'{constants.mark_1_red}'
                            if marks_red[6] == 3:
                                round_score += 25
                            else:
                                marks_red[6] += 1

                    elif score[1] == 'OUT':
                        round_marks += 0
                        round_marks_text += f'{constants.mark_0_red}'

                        if full_open_flag == True:
                            ignore_darts += 1

                    elif score[0] == '' or score[0] == 'S':
                        if int(score[1]) >= 15:
                            round_marks += 1
                            round_marks_text += f'{constants.mark_1_red}'
                            if marks_red[20 - int(score[1])] == 3:
                                round_score += int(score[1])
                            else:
                                marks_red[20 - int(score[1])] += 1
                        else:
                            round_marks += 0
                            round_marks_text += f'{constants.mark_0_red}'

                    elif score[0] == 'D':
                        if int(score[1]) >= 15:
                            round_marks += 2
                            round_marks_text += f'{constants.mark_2_red}'
                            if marks_red[20 - int(score[1])] == 3:
                                round_score += int(score[1]) * 2
                            elif marks_red[20 - int(score[1])] == 2:
                                marks_red[20 - int(score[1])] += 1
                                round_score += int(score[1])
                            else:
                                marks_red[20 - int(score[1])] += 2
                        else:
                            round_marks += 0
                            round_marks_text += f'{constants.mark_0_red}'

                    elif score[0] == 'T':
                        if int(score[1]) >= 15:
                            round_marks += 3
                            round_marks_text += f'{constants.mark_3_red}'
                            if marks_red[20 - int(score[1])] == 3:
                                round_score += int(score[1]) * 3
                            elif marks_red[20 - int(score[1])] == 2:
                                marks_red[20 - int(score[1])] += 1
                                round_score += int(score[1]) * 2
                            elif marks_red[20 - int(score[1])] == 1:
                                marks_red[20 - int(score[1])] += 2
                                round_score += int(score[1])
                            else:
                                marks_red[20 - int(score[1])] += 3
                        else:
                            round_marks += 0
                            round_marks_text += f'{constants.mark_0_red}'

                embed.description = marks_red_text

                field_name = embed.fields[0].name.split()
                player_name = field_name[1]
                current_score = int(field_name[2].replace('[', '').replace(']', ''))
                current_score += round_score
                current_marks = int(field_name[4])
                current_marks += round_marks
                embed.fields[0].name = f'🎯 {player_name} [{current_score}] (Total: {current_marks} marks)'

                field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                new_field_value = ''
                score_added_flag = False
                for value in field_value:
                    round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                    for round_data in round_parsed_data:
                        if round_data[1] != '':
                            new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                        elif score_added_flag == False:
                            current_round = int(round_data[0])
                            new_field_value += f'**R{round_data[0]}** {round_marks_text} [{round_score}] {round_score_text}\n'
                            score_added_flag = True

                for i in range(current_round + 1, 16):
                    new_field_value += f'**R{i:02}**\n'

                new_field_value += '\n'

                if current_round == 15 or full_open_flag == True:
                    new_field_value += 'Stats [ESTABLISHED]\n'
                    new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'

                    embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                    gameover_flag = True
                else:
                    new_field_value += 'Stats [REALTIME]\n'
                    new_field_value += f'**MPR** {current_marks / current_round:.2f} **MPD** {current_marks / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00'

                embed.fields[0].value = new_field_value

            else:
                target_score = int(embed.author.name)
                field_name = embed.fields[0].name.split()
                player_name = field_name[1]
                previous_score = int(field_name[2].replace('[', '').replace(']', ''))
                current_score = previous_score - round_score
                bust_flag = False
                ignore_darts = 0

                if current_score < 0:
                    bust_flag = True

                if current_score == 0:
                    ignore_darts = len(re.findall(r'(OUT)', round_score_text))

                if bust_flag == False:
                    embed.fields[0].name = f'🎯 {player_name} [{current_score}]'
                else:
                    embed.fields[0].name = f'🎯 {player_name} [{previous_score}]'

                field_value = re.findall(r'^.+$', embed.fields[0].value, re.MULTILINE)
                current_round = 1
                new_field_value = ''
                stats = []
                stats_established_flag = False

                score_added_flag = False
                for value in field_value:
                    round_parsed_data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
                    for round_data in round_parsed_data:
                        if round_data[1] != '':
                            new_field_value += f'**R{round_data[0]}** {round_data[1]}\n'
                        elif score_added_flag == False:
                            current_round = int(round_data[0])
                            if bust_flag == True:
                                new_field_value += f'**R{round_data[0]}** [BUST] {round_score_text}\n'
                            else:
                                new_field_value += f'**R{round_data[0]}** [{round_score}] {round_score_text}\n'
                            score_added_flag = True

                    established = re.findall(r'80% \(12R\) Stats \[(REALTIME|ESTABLISHED)\]', value)
                    if len(established) != 0 and established[0] == 'ESTABLISHED':
                        stats_established_flag = True

                    if value.startswith('**PP'):
                        stats.append(value)

                for i in range(current_round + 1, 16):
                    new_field_value += f'**R{i:02}**\n'

                new_field_value += '\n'

                if int(target_score * 0.2) > current_score:
                    new_field_value += '80% Stats [ESTABLISHED]\n'
                    if stats_established_flag == True:
                        new_field_value += f'{stats[0]}\n'
                    else:
                        if bust_flag == True:
                            new_field_value += f'{stats[0]}\n'
                        else:
                            new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                else:
                    if current_score == 0:
                        new_field_value += '80% Stats [ESTABLISHED]\n'
                    else:
                        new_field_value += '80% Stats [REALTIME]\n'

                    if bust_flag == True:
                        new_field_value += f'{stats[0]}\n'
                    else:
                        new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                new_field_value += '\n'

                if current_round == 15 or current_score == 0:
                    new_field_value += '100% Stats [ESTABLISHED]\n'

                    if bust_flag == True:
                        new_field_value += f'{stats[1]}\n'
                    else:
                        new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'
                    
                    embed.fields[0].name = embed.fields[0].name.replace('🎯 ', '')
                    gameover_flag = True
                else:
                    if current_score == 0:
                        new_field_value += '100% Stats [ESTABLISHED]\n'
                    else:
                        new_field_value += '100% Stats [REALTIME]\n'

                    if bust_flag == True:
                        new_field_value += f'{stats[1]}\n'
                    else:
                        new_field_value += f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / ((current_round * 3) - ignore_darts):.2f} **Rt** 0.00\n'

                embed.fields[0].value = new_field_value

        await client.message_edit(previous_message, embed = embed)
        await client.message_delete(message)
        if gameover_flag == True:
            if len(embed.fields) == 2:
                embed.fields[0].value = embed.fields[0].value.replace('REALTIME', 'ESTABLISHED')
                embed.fields[1].value = embed.fields[1].value.replace('REALTIME', 'ESTABLISHED')
            else:
                embed.fields[0].value = embed.fields[0].value.replace('REALTIME', 'ESTABLISHED')
            await client.message_edit(previous_message, embed = embed)
            await client.message_create(message.channel, 'GAME OVER!')

@Satori.events
async def ready(client):
    print(f'Logged in as {client:f} ({client.id})')

## Start
if __name__ == '__main__':
    Satori.start()
    wait_for_interruption()
