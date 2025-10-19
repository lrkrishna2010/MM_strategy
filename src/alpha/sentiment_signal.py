class SentimentSignal:
    def __init__(self, smooth=0.2):
        self.smooth = smooth
        self.last = 0.0

    def on_news(self, headline: str):
        mapping = {
            "beats": 0.2, "raises": 0.2, "strong": 0.168, "upbeat": 0.168,
            "upgrade": 0.166, "buyback": 0.148, "macro": 0.118, "confident": 0.294,
            "downgrade": -0.04, "resigns": -0.066, "disruption": -0.036, "probe": -0.04,
            "competitor": -0.042, "dividend": -0.052
        }
        score = 0.0
        h = headline.lower()
        for k,v in mapping.items():
            if k in h:
                score += v
        self.last = (1-self.smooth)*self.last + self.smooth*score
        return self.last
