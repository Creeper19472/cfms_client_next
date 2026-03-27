import random

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


__all__ = ["get_quote"]


class Quotes:
    def __init__(self) -> None:
        self.all_quotes = [
            _(
                "Stars hang low over the vast plain, the moon surges over the great river."
            ),
            _(
                "A true hero among mortals, no need to test their cry further."
            ),  # - Duan Chengji, Qingpingle
            _(
                "Drunk, I trim the lamp to examine my sword; in dreams I return to camps echoing with bugles."
            ),  # - Xin Qiji
            _(
                "Though lacking wings like the colorful phoenix to fly side by side, our hearts connect with the clarity of a rhinoceros horn."
            ),  # - Li Shangyin
            _(
                "Seeking each other on dream paths, amid flying rain and falling flowers."
            ),  # - Yan Jidao, Linjiangxian
        ]

    def refresh(self):
        self.__init__()


__quotes = Quotes()


def get_quote():
    return random.choice(__quotes.all_quotes)


def refresh_quote():
    __quotes.refresh()
