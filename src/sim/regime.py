import random

class Regime2State:
    CALM = 0; STRESS = 1
    def __init__(self, p_stay_calm=0.95, p_stay_stress=0.9):
        self.p_stay_calm = p_stay_calm; self.p_stay_stress = p_stay_stress; self.state = self.CALM
    def step(self):
        r = random.random()
        if self.state == self.CALM:
            if r > self.p_stay_calm: self.state = self.STRESS
        else:
            if r > self.p_stay_stress: self.state = self.CALM
        return self.state
