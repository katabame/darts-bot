import hata
import re
import utils

def create_embed(embed: hata.Embed, scores: list[list[str]]) -> tuple[hata.Embed, bool]:
    turn_index = 1 if len(embed.fields) == 2 and embed.fields[1].name.startswith('🎯') else 0
    field_value = re.findall(r'^.+$', embed.fields[turn_index].value, re.MULTILINE)
    total_rounds = int(embed.author.name.split()[1].replace('(', '').replace('R)', ''))
    field_name = embed.fields[turn_index].name.split()
    player_name = field_name[1]
    current_score = int(field_name[2].replace('[', '').replace(']', ''))
    stats_text, current_score, current_round = generate_stats(current_score, scores, total_rounds, field_value)
    embed.fields[turn_index].value = stats_text

    embed.fields[turn_index].name = f'{'' if len(embed.fields) == 2 else '🎯 '}{player_name} [{current_score}]'
    if len(embed.fields) == 2:
        embed.fields[1 - turn_index].name = f'🎯 {embed.fields[1 - turn_index].name}'

    is_gameover = current_round == total_rounds and turn_index == 1 if len(embed.fields) == 2 else current_round == total_rounds

    return embed, is_gameover

def generate_stats(current_score:int, scores: list[list[str]], total_rounds:int, field_value: list[str]):
    stats_text = ''
    current_round = 1
    score_added = False
    round_score, score_text = utils.calculate_score(scores)
    current_score += round_score

    for value in field_value:
        data = re.findall(r'\*\*R([0-1][0-9])\*\*(.*)', value)
        for datum in data:
            if datum[1] != '':
                stats_text += f'**R{datum[0]}** {datum[1]}\n'
            elif score_added == False:
                current_round = int(datum[0])
                score_added = True
                stats_text += f'**R{current_round:02}** [{round_score}] {score_text}\n'

    for i in range(current_round + 1, total_rounds + 1):
        stats_text += f'**R{i:02}**\n'

    stats_text += '\n'
    stats_text += f'Stats [{'ESTABLISHED' if current_round == total_rounds else 'REALTIME'}]\n'
    stats_text += f'**PPR** {current_score / current_round:.2f} **PPD** {current_score / (current_round * 3):.2f} **Rt** 0.00\n'

    return stats_text, current_score, current_round
