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


chat_id_IA = -1002392215111

channels_id = [
    -1001036240821, #https://t.me/meduzalive
    -1002066112684, #https://t.me/channelOut2
    -1001124373913, #'https://t.me/team_milov'
    # 'https://t.me/LipsitsIgor',
    # 'https://t.me/tvrain',
    # 'https://t.me/kaluginprofit',
]

key_words = [
    "apple",
    "iphone",
    "nvidia",
    "netflix",
    "openai",
    "маск",
    "tesla",
    "space",
    "chatgpt",
    "интеллект",
    "главные новости",
    "день войны:",
    "россия:",
    "бензин",
]
