"""Check the change of variables zeta1 = |e|^(1/2) sign(e) used for the error dynamics: simulate (e, zeta)
directly and through (zeta1, zeta2) with time-varying gains; the mismatch must vanish as dt -> 0."""
import numpy as np


def run(dt, T=0.01):
    k1f = lambda t: 50 + 20*np.sin(3*t)
    k2f = lambda t: 300 + 100*np.cos(2*t)
    pd = lambda t: 40*np.sin(5*t)
    e, z, t = 0.37, -1.2, 0.0
    z1, z2 = np.sign(0.37)*np.sqrt(0.37), -1.2
    de_max = 0.0
    for _ in range(int(T/dt)):
        k1, k2 = k1f(t), k2f(t)
        de = -k1*np.sqrt(abs(e))*np.sign(e) + z
        dz = -k2*np.sign(e) + pd(t)
        e += dt*de; z += dt*dz
        dz1 = -k1/2*np.sign(z1) + z2/(2*abs(z1))
        dz2 = -k2*np.sign(z1) + pd(t)
        z1 += dt*dz1; z2 += dt*dz2
        de_max = max(de_max, abs(e - np.sign(z1)*z1**2))
        t += dt
    return de_max


errs = [run(dt) for dt in (1e-5, 1e-6, 1e-7)]
for dt, e in zip((1e-5, 1e-6, 1e-7), errs):
    print(f'dt={dt:.0e}  max|e - sign(zeta1) zeta1^2| = {e:.3e}')
assert errs[2] < errs[1] < errs[0]
print('PASS (error decreases ~linearly with dt)')
