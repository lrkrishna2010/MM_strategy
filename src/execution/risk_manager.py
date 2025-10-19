class RiskManager:
    def __init__(self, inv_limit: int):
        self.inv_limit = inv_limit

    def capped_size(self, inv: int, base_size: int) -> int:
        room = self.inv_limit - abs(inv)
        return max(0, min(base_size, room))
