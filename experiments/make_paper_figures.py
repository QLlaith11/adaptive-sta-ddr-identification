"""Regenerate the two paper figures (written to ../paper/).
Fig. 1: tracking and adaptive-gain trajectory (nominal plant, 6 s, dt = 2e-5 s).
Fig. 2: observer RMS error and regressor condition number per trajectory (from results/trajectory.json)."""
import json, pathlib, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ddr_sta.core_sim import run_pipeline
from ddr_sta import excitation as ex

plt.rcParams.update({'font.family': 'serif', 'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7,
                     'ytick.labelsize': 7, 'legend.fontsize': 7, 'axes.linewidth': 0.6, 'lines.linewidth': 1.0})
OUT = ROOT / 'paper'

# ---- Fig. 1 ----
uR, uL = ex.multisine()
tR, tL = ex.get_torque(0.0)
dt = 2e-5
res = run_pipeline(2.5, 0.03, 1e-4, uR, uL, tR, tL, observer_type='adaptive', T=6.0, dt=dt, warmup=0.5)
t = np.arange(len(res['wR_true'])) * dt
print(f"Fig.1 data: max kappa1 = {np.nanmax(res['k1R']):.1f}, mean kappa1 (t>1 s) = {np.nanmean(res['k1R'][t > 1]):.1f}")
fig, ax = plt.subplots(2, 1, figsize=(3.4, 3.0), sharex=True)
ax[0].plot(t, res['wR_true'], color='black', label=r'true $\omega_R$')
ax[0].plot(t, res['wR_hat'], color='#B22222', lw=0.8, ls='--', label=r'$\hat\omega_R$ (adaptive)')
ax[0].set_ylabel('wheel speed [rad/s]')
ax[0].legend(loc='upper right', frameon=False, handlelength=1.5)
ax[1].plot(t, res['k1R'], color='black')
ax[1].set_ylabel(r'$\kappa_{1,R}(t)$')
ax[1].set_xlabel('time [s]')
plt.tight_layout(pad=0.3)
plt.savefig(OUT / 'fig_paper_tracking.pdf')
plt.close()

# ---- Fig. 2 ----
tj = json.load(open(ROOT / 'results' / 'trajectory.json'))
order = ex.TRAJECTORIES
labels = ['Common-\nmode', 'Minimal\ndiff.', 'Multi-\nsine', 'PRBS', 'Chirp', 'Figure-\neight']
rms = [np.mean([r['obs_rms_pct'] for r in tj['monte_carlo'] if r['traj'] == k]) for k in order]
cond = [[r['cond'] for r in tj['conditioning'] if r['traj'] == k][0] for k in order]
fig, ax1 = plt.subplots(figsize=(3.4, 2.5))
x = np.arange(len(order))
ax1.bar(x - 0.175, rms, width=0.35, color='0.35', label='observer RMS error (%)')
ax1.set_ylabel('observer RMS error (%)')
ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=6.3)
ax2 = ax1.twinx()
ax2.plot(x, cond, 'o-', color='black', markersize=4, label='regressor condition number')
ax2.set_yscale('log'); ax2.set_ylabel('regressor condition number')
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper center', frameon=False, fontsize=6.3)
plt.tight_layout(pad=0.3)
plt.savefig(OUT / 'fig_paper_traj.pdf')
print('figures written to', OUT)
