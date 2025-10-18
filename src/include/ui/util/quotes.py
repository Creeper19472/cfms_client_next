import random

import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


__all__ = ["get_quote"]

ALL_QUOTES = [
    _("星垂平野阔，月涌大江流。"),
    _("自是人间英物，不须更试啼声。"), # - Duan Chengji, Qingpingle
    _("醉里挑灯看剑，梦回吹角连营。"), # - Xin Qiji
    _("身无彩凤双飞翼，心有灵犀一点通。"), # - Li Shangyin
    _("相寻梦里路，飞雨落花中。"), # - Yan Jidao, Linjiangxian
]

def get_quote():
    return random.choice(ALL_QUOTES)