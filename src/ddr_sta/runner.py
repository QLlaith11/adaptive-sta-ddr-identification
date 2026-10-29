"""Single-task runner shared by all experiment scripts (picklable, so it works with multiprocessing)."""
import numpy as np
from .core_sim import run_pipeline
from . import excitation as ex

DEFAULTS = dict(m=2.5, Iz=0.03, Jw=1e-4, traj='multisine', u_scale=1.0, tau_amp=0.0,
                observer='adaptive', sigma_i=0.0, seed=0, eps=None,
                T=4.0, dt=5e-5, filt_pole=1.0, warmup=1.5)


def run_task(task):
    p = {**DEFAULTS, **task}
    uR, uL = ex.get_trajectory(p['traj'], p['u_scale'])
    tauR, tauL = ex.get_torque(p['tau_amp'])
    adapt = None
    if p['observer'] == 'adaptive':
        eps = p['eps'] if p['eps'] is not None else max(1e-4, 3 * p['sigma_i'])
        adapt = dict(kappa1_0=1.0, kappa1_min=1.0, growth_rate=2000.0, rho=88.0, eps=eps)
    res = run_pipeline(p['m'], p['Iz'], p['Jw'], uR, uL, tauR, tauL,
                       observer_type=p['observer'], adapt_kwargs=adapt, T=p['T'], dt=p['dt'],
                       filt_pole=p['filt_pole'], sigma_i=p['sigma_i'], seed=p['seed'], warmup=p['warmup'])
    a, bt, c = res['theta_final']
    at, btrue, vtrue = res['alpha_true'], res['beta_true'], res['b_true']
    n = len(res['wR_true'])
    mask = np.arange(n) * p['dt'] > p['warmup']
    sv = np.linalg.svd(np.linalg.inv(res['rls_P']) - np.eye(3) / res['rls_delta'], compute_uv=False)
    return dict(alpha_true=float(at), beta_true=float(btrue),
                a_err=float(100 * (a - at) / at),
                beta_err_pct=float(100 * (bt - btrue) / btrue),
                beta_err_norm=float(100 * (bt - btrue) / at),   # |beta error| / alpha_true
                v_err=float(100 * (c - vtrue) / vtrue),
                obs_rms_pct=float(res['obs_rms_pct']), speed_scale=float(res['speed_scale']),
                bias_R=float(np.mean(res['wR_true'][mask] - res['wR_hat'][mask])),
                sigma_min=float(sv.min()), sigma_max=float(sv.max()), cond=float(sv.max() / sv.min()),
                k1_max=float(np.nanmax(res['k1R'])) if p['observer'] == 'adaptive' else None)
