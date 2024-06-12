from dataclasses import dataclass
from environs import Env


@dataclass
class Client:
    api_id: int
    api_hash: str


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    client: Client


def Load_config():
    env: Env = Env()
    env.read_env()
    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN')
        ),
        client=Client(
            api_id=env('API_ID'),
            api_hash=env('API_HASH')
        )
    )


group_IA_id = -4246635872
channel_out_id = -1002066112684

channels_id = [
    -1001324653248,  # ИнфоПовод
    -1001095950024,  # bdtprb
    -1001521490869,  # LipsitsIgor
    -1001005031786,  # tvrain
    -1001036240821,  # meduzalive
    -1002066112684,  # channel_out_id
]

key_words = [
    "пробк",
    "apple",
    "open ai",
    "маск",
    "tesla",
    "интеллект",
    "национализаци",
    "мобилизаци",
    "доллар",
    "беспилотник",
    "бпла",
    "квадрокоптер",
    "главные новости",
    "главное за",
    "итоги дня",
    "итоги недели",
    "утро на дожде",
]

key_words2 = [
    "главные новости",
    "главное за",
    "итоги дня",
    "итоги недели",
    "утро на дожде",
]

key_words_not = [
    "скидки",
    # "акции",
    # "подписывайтесь",
    "приглашаем",
    "вакансии",
    "зарплата",
]
