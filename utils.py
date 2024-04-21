import hata
import random
import constants

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

    if game == 'STANDARD CRICKET':
        start_score = '0'
        additional_text = '(Total: 0 marks)'
    elif game == 'COUNT-UP':
        start_score = '0'
        additional_text = ''
    else:
        start_score = game
        additional_text = ''

    embed.add_field(
        name = f'🎯 {red.display_name} [{"0" if game == "STANDARD CRICKET" or game == "COUNT-UP" else game}] {"(Total: 0 marks)" if game == "STANDARD CRICKET" else ""}',
        value  = stats_template,
        inline = True
    )
    if blue:
        embed.add_field(
            name = f'{blue.display_name} [{"0" if game == "STANDARD CRICKET" or game == "COUNT-UP" else game}] {"(Total: 0 marks)" if game == "STANDARD CRICKET" else ""}',
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
            score_text += f'{"" if score[0] in ["", "S"] else score[0]}{score[1]} '
            total_score += int(score[1] * multiplier)

    return total_score, score_text

def calculate_mark(scores: list[list[str]], marks_red: list[int], marks_blue: list[int] | None, turn_index: int):
    total_score: int = 0
    total_mark: int = 0
    mark_text = ''

    marks_ally = marks_red if turn_index == 0 else marks_blue
    marks_opponent = marks_blue if turn_index == 0 else marks_red

    for score in scores:
        if score[1] == 'BULL':
            if score[0] == 'D':
                if len(marks_opponent) > 0 and marks_opponent[6] == 3:
                    mark = 0 if marks_ally[6] == 3 else 1 if marks_ally[6] == 2 else 2
                else:
                    mark = 2
                    total_score += 50 if marks_ally[6] == 3 else 25 if marks_ally[6] == 2 else 0
            else:
                if len(marks_opponent) > 0 and marks_opponent[6] == 3:
                    mark = 0 if marks_ally[6] == 3 else 1
                else:
                    mark = 1
                    total_score += 25 if marks_ally[6] == 3 else 0
            marks_ally[6] += mark
        elif score[1] == 'OUT':
            mark = 0
        else:
            if int(score[1]) < 15:
                mark = 0
            else:
                score_index = 20 - int(score[1])
                multiplier: int = 3 if score[0] == 'T' else 2 if score[0] == 'D' else 1\

                if len(marks_opponent) > 0 and marks_opponent[score_index] == 3:
                    if multiplier == 3:
                        mark = 0 if marks_ally[score_index] == 3 else 1 if marks_ally[score_index] == 2 else 2 if marks_ally[score_index] == 1 else multiplier
                    else:
                        mark = 0 if marks_ally[score_index] == 3 else 1 if marks_ally[score_index] == 2 else multiplier
                else:
                    mark = multiplier
                    if multiplier == 3:
                        total_score += multiplier * int(score[1]) if marks_ally[score_index] == 3 else 2 * int(score[1]) if marks_ally[score_index] == 2 else 1 * int(score[1]) if marks_ally[score_index] == 1 else 0
                    elif multiplier == 2:
                        total_score += multiplier * int(score[1]) if marks_ally[score_index] == 3 else 1 * int(score[1]) if marks_ally[score_index] == 2 else 0
                    else:
                        total_score += multiplier * int(score[1]) if marks_ally[score_index] == 3 else 0
                marks_ally[score_index] = min(marks_ally[score_index] + mark, 3)
        total_mark += mark
        
        if mark == 0:
            mark_text += '0 '
        elif mark == 1:
            mark_text += '1 '
        elif mark == 2:
            mark_text += '2 '
        else:
            mark_text += '3 '

    marks_red = marks_ally if turn_index == 0 else marks_opponent
    marks_blue = marks_opponent if turn_index == 0 else marks_ally
    return total_score, total_mark, mark_text, marks_red, marks_blue
