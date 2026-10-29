"""Table II / Fig. 2: excitation-trajectory comparison (nominal plant, 5 mA noise, Monte Carlo)
plus a noise-free run per trajectory for the regressor conditioning (singular values of Phi^T Phi)."""
import sys
from common import parser, run_parallel, save
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'src'))
from ddr_sta.excitation import TRAJECTORIES

p = parser(__doc__)
p.add_argument('--n-trials', type=int, default=6)
a = p.parse_args()
n_tr, T = (2, 2.0) if a.quick else (a.n_trials, 4.0)
trajs = ['common_mode', 'multisine', 'figure_eight'] if a.quick else TRAJECTORIES

mc = run_parallel([dict(traj=t, sigma_i=0.005, seed=400 + k, T=T) for t in trajs for k in range(n_tr)], a.jobs)
cond = run_parallel([dict(traj=t, sigma_i=0.0, seed=0, T=T) for t in trajs], a.jobs)
save('trajectory.json', dict(n_trials=n_tr, monte_carlo=mc, conditioning=cond), a.quick)
