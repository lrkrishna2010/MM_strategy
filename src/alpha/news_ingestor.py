from dataclasses import dataclass

@dataclass
class NewsItem:
    ts: int
    headline: str

def synthetic_news_tape(symbol: str):
    items = [
        NewsItem(0, "Company beats earnings and raises guidance"),
        NewsItem(50, "Analyst downgrades on valuation concerns"),
        NewsItem(100, "Product launch receives strong early reviews"),
        NewsItem(150, "CFO resigns unexpectedly"),
        NewsItem(250, "Large buyback announced by board"),
        NewsItem(300, "Macro: rates surprise to upside"),
        NewsItem(350, "CEO interview: confident on growth"),
        NewsItem(450, "Supply chain disruption in a key region"),
    ]
    return items
