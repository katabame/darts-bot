import hata
import re
import utils

def create_embed(embed: hata.Embed, scores: list[list[str]]) -> tuple[hata.Embed, bool]:
    turn_index = 1 if len(embed.fields) == 2 and embed.fields[1].name.startswith('🎯') else 0
    field_value = re.findall(r'^.+$', embed.fields[turn_index].value, re.MULTILINE)
    field_name = embed.author.name.split()
    total_rounds = int(field_name[1].replace('(', '').replace('R)', ''))
    target_score = int(field_name[0])
    field_name = embed.fields[turn_index].name.split()
    player_name = field_name[1]
    current_score = int(field_name[2].replace('[', '').replace(']', ''))
    stats_text, current_score, current_round = generate_stats(current_score, scores, total_rounds, field_value, target_score)
    embed.fields[turn_index].value = stats_text

    embed.fields[turn_index].name = f'{'' if len(embed.fields) == 2 else '🎯 '}{player_name} [{current_score}]'
    if len(embed.fields) == 2:
        embed.fields[1 - turn_index].name = f'🎯 {embed.fields[1 - turn_index].name}'

    is_gameover = current_score == 0 or (current_round == total_rounds and turn_index == 1) if len(embed.fields) == 2 else current_score == 0 or current_round == total_rounds

    return embed, is_gameover

def generate_stats(current_score:int, scores: list[list[str]], total_rounds:int, field_value: list[str], target_score: int):
    stats_text = ''
    current_round = 1
    score_added = False
    established = False
    stats = []
    round_score, score_text = utils.calculate_score(scores)
    previous_score = current_score
    current_score -= round_score
    busted = 0 > current_score
    if busted:
        current_score = previous_score
    ignore_darts = 0
    if current_score == 0:
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
                stats_text += f'**R{current_round:02}** [BUST] {score_text}\n' if busted else f'**R{current_round:02}** [{round_score}] {score_text}\n'
        est = re.findall(r'80% Stats \[(REALTIME|ESTABLISHED)\]', value)
        established = est[0] == 'ESTABLISHED' if len(est) > 0 else False
        if value.startswith('**PP'):
            stats.append(value)

    for i in range(current_round + 1, total_rounds + 1):
        stats_text += f'**R{i:02}**\n'

    stats_text += '\n'
    stats_text += f'80% Stats [{'ESTABLISHED' if established else 'REALTIME'}]\n'
    stats_text += f'{stats[0]}\n' if established or busted else f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / (current_round * 3 - ignore_darts):.2f} **Rt** 0.00\n'
    stats_text += '\n'
    stats_text += f'100% Stats [{'ESTABLISHED' if current_round == total_rounds else 'REALTIME'}]\n'
    stats_text += f'{stats[1]}\n' if busted else f'**PPR** {(target_score - current_score) / current_round:.2f} **PPD** {(target_score - current_score) / (current_round * 3 - ignore_darts):.2f} **Rt** 0.00\n'

    return stats_text, current_score, current_round
