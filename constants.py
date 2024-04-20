from hata import Emoji

games = {
    '301': '301', '501': '501', '701': '701',
    '901': '901', '1101': '1101', '1501': '1501',
    'STANDARD CRICKET': 'STANDARD CRICKET',
    'COUNT-UP': 'COUNT-UP'
}

stats_countup = """
**R01**
**R02**
**R03**
**R04**
**R05**
**R06**
**R07**
**R08**

Stats [REALTIME]
**PPR** 0.00 **PPD** 0.00 **Rt** 0.00
"""

stats_01 = """
**R01**
**R02**
**R03**
**R04**
**R05**
**R06**
**R07**
**R08**
**R09**
**R10**
**R11**
**R12**
**R13**
**R14**
**R15**

80% Stats [REALTIME]
**PPR** 0.00 **PPD** 0.00 **Rt** 0.00

100% Stats [REALTIME]
**PPR** 0.00 **PPD** 0.00 **Rt** 0.00
"""

stats_cricket = """
**R01**
**R02**
**R03**
**R04**
**R05**
**R06**
**R07**
**R08**
**R09**
**R10**
**R11**
**R12**
**R13**
**R14**
**R15**

Stats [REALTIME]
**MPR** 0.00 **MPD** 0.00 **Rt** 0.00
"""

marks_red_only = """
<:0marks_red:1229626995659243520> **20**
<:0marks_red:1229626995659243520> **19**
<:0marks_red:1229626995659243520> **18**
<:0marks_red:1229626995659243520> **17**
<:0marks_red:1229626995659243520> **16**
<:0marks_red:1229626995659243520> **15**
<:0marks_red:1229626995659243520> **BULL**
"""

marks = """
<:0marks_red:1229626995659243520> **20** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **19** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **18** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **17** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **16** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **15** <:0marks_blue:1229627078765314139>
<:0marks_red:1229626995659243520> **BULL** <:0marks_blue:1229627078765314139>
"""

mark_0_red        = Emoji.precreate(1229626995659243520)
mark_1_red        = Emoji.precreate(1229626931281006732)
mark_2_red        = Emoji.precreate(1229626917674549340)
mark_3_red        = Emoji.precreate(1229626889778237523)
mark_3_red_close  = Emoji.precreate(1229626877124284466)

mark_0_blue       = Emoji.precreate(1229627078765314139)
mark_1_blue       = Emoji.precreate(1229627066325012511)
mark_2_blue       = Emoji.precreate(1229627053884575806)
mark_3_blue       = Emoji.precreate(1229627041406652436)
mark_3_blue_close = Emoji.precreate(1229627029926842449)

color_01      = 0xff3030
color_countup = 0x30ff30
color_cricket = 0x3030ff
color_party   = 0xff3090
