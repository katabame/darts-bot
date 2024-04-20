import hata
import random
import constants

#def cointoss(head: str | hata.User, tail: str | hata.User) -> tuple[str | hata.User]:
#    coin = [head, tail]
#    win = random.choise(coin)
#    print('win', win)
#    coin.remove(win)
#    lose = coin[0]
#    print(win, lose)
#    return win, lose

def create_start_message(red: hata.User, blue: hata.User | None) -> str:
    if blue is None:
        return f'<@{red.id}> GAME ON!'
    else:
        return f'<@{red.id}> vs <@{blue.id}> GAME ON!'

def create_game_embed(game: str, red: hata.User, blue: hata.User | None, rounds: int = None) -> hata.Embed:
    embed = hata.Embed()

    if game == 'STANDARD CRICKET':
        stats_template    = constants.stats_cricket
        embed.color       = constants.color_cricket
        embed.description = constants.marks if blue else constants.marks_red_only
        rounds = 15 if rounds is None else rounds
    elif game == 'COUNT-UP':
        stats_template    = constants.stats_countup
        embed.color       = constants.color_countup
        rounds = 8 if rounds is None else rounds
    else:
        stats_template    = constants.stats_01
        embed.color       = constants.color_01
        rounds = 15 if rounds is None else rounds
    
    embed.add_author(f'{game} ({rounds}R)')
    embed.title = f'{red.display_name} vs {blue.display_name}' if blue else f'{red.display_name}'

    embed.add_field(
        name   = f'🎯 {red.display_name} [{'0' if game == 'STANDARD CRICKET' or game == 'COUNT-UP' else game}] {'(Total: 0 marks)' if game == 'STANDARD CRICKET' else ''}',
        value  = stats_template,
        inline = True
    )
    if blue:
        embed.add_field(
            name   = f'{blue.display_name} [{'0' if game == 'STANDARD CRICKET' or game == 'COUNT-UP' else game}] {'(Total: 0 marks)' if game == 'STANDARD CRICKET' else ''}',
            value  = stats_template,
            inline = True
        )

    return embed

def determine_teams(event_user: hata.User, player1: hata.User | None, player2: hata.User | None, toss: bool = False) -> tuple[hata.User | None]:
    if player1 is None and player2 is None:
        return event_user, None
    elif player1 and player2 is None:
        return player1, None
    elif player1 is None and player2:
        return player2, None
    else:
        if toss:
            players = [player1, player2]
            red = random.choice(players)
            players.remove(red)
            blue = players[0]

            return red, blue
        else:
            return player1, player2

#def is_round_over(current_round: int, total_round: int, is_solo: bool = False, is_blue_turn: bool = False) -> bool:
#    return current_round >= total_round and (is_solo or is_blue_turn)

def calculate_score(scores: list[list[str]], separate_bull: bool = False) -> tuple[int, str]:
    total_score: int = 0
    score_text: str = ''

    for score in scores:
        if score[1] == 'BULL':
            if score[0] == 'D':
                score_text += 'D-BULL '
                total_score += 50
            else:
                score_text += 'BULL '
                total_score += 25 if separate_bull else 50
        elif score[1] == 'OUT':
            score_text += 'OUT '
        else:
            multiplier: int = 3 if score[0] == ['T'] else 2 if score[0] == 'D' else 1
            score_text += f'{'' if score[0] in ['', 'S'] else score[0]}{score[1]} '
            total_score += int(score[1] * multiplier)

    return total_score, score_text
