from dataclasses import dataclass


@dataclass
class Rule:
kind: str # gte, lte, cross_up
threshold: float
state_prev: float | None = None


def match(self, price: float) -> bool:
    if self.kind == "gte":
        return price >= self.threshold
    if self.kind == "lte":
        return price <= self.threshold
    if self.kind == "cross_up":
        if self.state_prev is None:
            self.state_prev = price
            return False
        hit = self.state_prev < self.threshold <= price
        self.state_prev = price
        return hit
    return False