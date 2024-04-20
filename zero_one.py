import hata
import utils

def create_embed(embed: hata.Embed) -> tuple[hata.Embed, bool]:
    is_gameover = False
    utils.calculate_score()
    return embed, is_gameover
