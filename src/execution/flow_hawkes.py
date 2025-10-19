import random, math

class Hawkes1D:
    def __init__(self, mu=0.5, alpha=0.6, beta=0.3):
        self.mu = mu; self.alpha = alpha; self.beta = beta; self.lambda_t = mu

    def step_intensity(self, n_events_last_step=0):
        self.lambda_t = self.mu + self.alpha * n_events_last_step + (1 - self.beta) * (self.lambda_t - self.mu)
        self.lambda_t = max(1e-6, self.lambda_t); return self.lambda_t

    def sample_events(self):
        lam = min(self.lambda_t, 10.0)
        p0 = math.exp(-lam); p1 = lam * p0
        r = random.random()
        if r < p0: return 0
        if r < p0 + p1: return 1
        return 2
