"""Excitation trajectories (applied voltages) and load-torque disturbances."""
import numpy as np


def multisine(u_scale=1.0):
    def uR(t):
        return u_scale * (12 * np.sin(2*np.pi*0.5*t) + 4 * np.sin(2*np.pi*3*t) + 2 * np.sin(2*np.pi*7*t))
    def uL(t):
        return u_scale * (12 * np.sin(2*np.pi*0.5*t + 0.3) + 4 * np.sin(2*np.pi*3.3*t) + 2 * np.sin(2*np.pi*7.7*t))
    return uR, uL


def _common_mode(t):
    u = 12 * np.sin(2*np.pi*0.5*t) + 4 * np.sin(2*np.pi*3*t) + 2 * np.sin(2*np.pi*7*t)
    return u, u


def _min_differential(t):
    common = 10 * np.sin(2*np.pi*0.7*t)
    diff = 2 * np.sin(2*np.pi*1.3*t)
    return common + diff, common - diff


def _prbs_factory(seed=7, switch_dt=0.05, amp=10.0):
    rng = np.random.default_rng(seed)
    n_sw = int(20 / switch_dt) + 10
    seqR = rng.choice([-1, 1], n_sw)
    seqL = rng.choice([-1, 1], n_sw)
    def f(t):
        idx = min(int(t / switch_dt), n_sw - 1)
        return amp * seqR[idx], amp * seqL[idx]
    return f


def _chirp(t):
    f0, f1, Tc = 0.2, 8.0, 4.0
    ph = 2*np.pi*(f0*t + (f1 - f0)*t**2/(2*Tc))
    common = 10 * np.sin(ph)
    diffph = 2*np.pi*(0.3*f0*t + 0.3*(f1 - f0)*t**2/(2*Tc) + 0.5)
    diff = 4 * np.sin(diffph)
    return common + diff, common - diff


def _figure_eight(t):
    period = 2.0
    phase = (t % period) / period
    drive = 10 * np.sign(np.sin(2*np.pi*t/period)) * (1 - np.exp(-8*np.minimum(phase, 1 - phase)))
    turn = 5 * np.sin(2*np.pi*t/1.3)
    return drive + turn, drive - turn


TRAJECTORIES = ['common_mode', 'min_differential', 'multisine', 'prbs', 'chirp', 'figure_eight']


def get_trajectory(name, u_scale=1.0):
    """Return (uR(t), uL(t)) for a named trajectory."""
    if name == 'multisine':
        return multisine(u_scale)
    f = {'common_mode': _common_mode, 'min_differential': _min_differential,
         'prbs': _prbs_factory(), 'chirp': _chirp, 'figure_eight': _figure_eight}[name]
    return (lambda t: u_scale * f(t)[0]), (lambda t: u_scale * f(t)[1])


def get_torque(amp=0.0):
    """Unmodeled sinusoidal load-torque disturbance, per-channel amplitude `amp` [N m]."""
    return (lambda t: amp * np.sin(2*np.pi*1.1*t + 1.0)), (lambda t: amp * np.sin(2*np.pi*1.3*t + 0.5))
