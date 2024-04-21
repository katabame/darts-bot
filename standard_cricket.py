import hata
import re
import utils
import constants

def create_embed(embed: hata.Embed, scores: list[list[str]]) -> tuple[hata.Embed, bool]:
    turn_index = 1 if len(embed.fields) == 2 and embed.fields[1].name.startswith('🎯') else 0
    field_value = re.findall(r'^.+$', embed.fields[turn_index].value, re.MULTILINE)
    total_rounds = int(embed.author.name.split()[2].replace('(', '').replace('R)', ''))
    field_name = embed.fields[turn_index].name.split()
    player_name = field_name[1]
    current_score = int(field_name[2].replace('[', '').replace(']', ''))
    current_mark = int(field_name[4])
    marks_red = []
    marks_blue = []

    target_marks = re.findall(r'^.+$', embed.description, re.MULTILINE)
    for target_mark in target_marks:
        mark_red = re.findall(r'.*([0-3])marks_red.*', target_mark)
        marks_red.append(int(mark_red[0]))
        mark_blue = re.findall(r'.*([0-3])marks_blue.*', target_mark)
        if len(mark_blue) > 0:
            marks_blue.append(int(mark_blue[0]))

    stats_text, current_score, current_round, current_mark, marks_red, marks_blue = generate_stats(current_score, scores, total_rounds, field_value, current_mark, marks_red, marks_blue, turn_index)
    embed.fields[turn_index].value = stats_text
    embed.description = generate_marks_text(marks_red, marks_blue)
    embed.fields[turn_index].name = f'{"" if len(embed.fields) == 2 else "🎯 "}{player_name} [{current_score}] (Total: {current_mark} marks)'
    if len(embed.fields) == 2:
        embed.fields[1 - turn_index].name = f'🎯 {embed.fields[1 - turn_index].name}'

    is_gameover = current_round == total_rounds
    if len(embed.fields) == 2:
        if marks_red.count(3) == len(marks_red) and marks_blue.count(3) == len(marks_blue):
            is_gameover = True
    else:
        if marks_red.count(3) == len(marks_red):
            is_gameover = True

    return embed, is_gameover

def generate_stats(current_score:int, scores: list[list[str]], total_rounds:int, field_value: list[str], current_mark: int, marks_red, marks_blue, turn_index):
    stats_text = ''
    current_round = 1
    score_added = False
    round_score, round_mark, mark_text, marks_red, marks_blue = utils.calculate_mark(scores, marks_red, marks_blue, turn_index)
    current_score += round_score
    current_mark += round_mark
    ignore_darts = 0

    marks_ally = marks_red if turn_index == 0 else marks_blue

    if marks_ally.count(3) == len(marks_ally):
        for score in scores:
            ignore_darts += 1 if score[1] == 'OUT' else 0

    for value in field_value:
        data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
        for datum in data:
            if datum[1] != '':
                stats_text += f'**R{datum[0]}** {datum[1]}\n'
            elif score_added == False:
                current_round = int(datum[0])
                score_added = True
                stats_text += f'**R{current_round:02}** [{round_score}] {mark_text}\n'

    for i in range(current_round + 1, total_rounds + 1):
        stats_text += f'**R{i:02}**\n'

    stats_text += '\n'
    stats_text += f'Stats [{"ESTABLISHED" if current_round == total_rounds else "REALTIME"}]\n'
    stats_text += f'**MPR** {current_mark / current_round:.2f} **MPD** {current_mark / (current_round * 3 - ignore_darts):.2f} **Rt** 0.00\n'

    return stats_text, current_score, current_round, current_mark, marks_red, marks_blue

def generate_marks_text(marks_red, marks_blue):
    marks_text = ''

    if len(marks_blue) > 0:
        for i in range(0, 7):
            if i == 6:
                if marks_red[i] == 3:
                    if marks_blue[i] == 3:
                        marks_text += f'{constants.mark_3_red_close} ~~**BULL**~~ {constants.mark_3_blue_close}\n'
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
                        marks_text += f'{constants.mark_3_red_close} ~~**{20 - i}**~~ {constants.mark_3_blue_close}\n'
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
    else:
        for i in range(0, 7):
            if i == 6:
                if marks_red[i] == 3:
                    marks_text += f'{constants.mark_3_red} **BULL**\n'
                elif marks_red[i] == 2:
                    marks_text += f'{constants.mark_2_red} **BULL**\n'
                elif marks_red[i] == 1:
                    marks_text += f'{constants.mark_1_red} **BULL**\n'
                else:
                    marks_text += f'{constants.mark_0_red} **BULL**\n'

            else:
                if marks_red[i] == 3:
                    marks_text += f'{constants.mark_3_red} **{20 - i}**\n'
                elif marks_red[i] == 2:
                    marks_text += f'{constants.mark_2_red} **{20 - i}**\n'
                elif marks_red[i] == 1:
                    marks_text += f'{constants.mark_1_red} **{20 - i}**\n'
                else:
                    marks_text += f'{constants.mark_0_red} **{20 - i}**\n'

    return marks_text
