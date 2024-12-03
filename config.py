from dataclasses import dataclass
from environs import Env


@dataclass
class Client:
    api_id: int
    api_hash: str


@dataclass
class TgBot:
    token: str
    admin_ids: []


@dataclass
class Config:
    tg_bot: TgBot
    client: Client


def load_config():
    env: Env = Env()
    env.read_env()
    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=[995657021,]
        ),
        client=Client(
            api_id=env('API_ID'),
            api_hash=env('API_HASH')
        )
    )


group_ia_id = -1002392215111

channels_id = [
    'https://t.me/meduzalive',
    'https://t.me/channelOut2',
    # 'https://t.me/LipsitsIgor',
    # 'https://t.me/tvrain',
    # 'https://t.me/kaluginprofit',
]

key_words = [
    "apple",
    "open ai",
    "илон",
    "tesla",
    "интеллект",
    "национализаци",
    "мобилизаци",
    "доллар",
    "курс рубля",
    "беспилотник",
    "бпла",
    "квадрокоптер",
    "главные новости",
    "главное",
    "блокиров",
    "уфа",
    "башкор",
    "башкир",
    "самолет",
    "отопление",
    "авария",
    "переведи",
]

key_words2 = [
    "уфа",
    "башкор",
    "башкир",
]

key_words_not = [
    "скидки",
    "приглашаем",
    "вакансии",
    "зарплата",
]
