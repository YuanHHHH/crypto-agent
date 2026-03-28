from pydantic import BaseModel

class CoinPrice(BaseModel):
    symbol: str
    price: float
    change_24h: float

class MarketOverview(BaseModel):
    total_market_cap_usd: float
    total_volume_usd: float
    btc_dominance: float
    eth_dominance: float
    market_cap_change_24h: float
    active_cryptocurrencies: int

class PriceHistory(BaseModel):
    symbol: str
    price: float
    change_24h: float
    time: str

class CoinMarket(BaseModel):
    symbol: str
    market_cap: float
    total_volume: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    ath: float

class Analysis(BaseModel):
    symbol: str
    content: str