"""Numerical/symbolic check of Proposition III.2: kappa1 >= max(2L/rho, 6 rho) implies
kappa2 = rho*kappa1 > L and kappa1^2 >= 4L(kappa2+L)/(kappa2-L)."""
import random
import sympy as sp

k1, L, rho = sp.symbols('kappa1 Lambda rho', positive=True)
W = rho * k1
print('kappa2 - Lambda          =', sp.simplify(W - L))
print('4L(kappa2+L)/(kappa2-L)  =', sp.simplify(4 * L * (W + L) / (W - L)))

random.seed(0)
m1 = m2 = 1e18
for _ in range(20000):
    Lv, rv = random.uniform(1e-6, 1e6), random.uniform(1e-6, 1e3)
    kv = max(2 * Lv / rv, 6 * rv) * 1.0000001
    Wv = rv * kv
    m1 = min(m1, Wv - Lv)
    m2 = min(m2, kv**2 - 4 * Lv * (Wv + Lv) / (Wv - Lv))
print(f'worst-case margin, condition 1: {m1:.3g} (must be > 0)')
print(f'worst-case margin, condition 2: {m2:.3g} (must be >= 0)')
assert m1 > 0 and m2 >= 0
print('PASS')
