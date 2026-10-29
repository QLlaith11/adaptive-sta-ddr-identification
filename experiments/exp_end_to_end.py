"""End-to-end identification accuracy, adaptive- vs constant-gain-fed pipeline, three scenarios.
Zero-noise scenarios are deterministic (n=1); the noisy scenario uses n=8 seeds."""
from common import parser, run_parallel, save

p = parser(__doc__)
a = p.parse_args()
T = 2.0 if a.quick else 4.0
scen = [('clean', 0.0, 0.0, 1), ('disturbance', 0.0035, 0.0, 1), ('disturbance+5mA', 0.0035, 0.005, 2 if a.quick else 8)]
tasks = [dict(scenario=n, observer=o, tau_amp=tau, sigma_i=s, seed=100 + k, T=T)
         for n, tau, s, nt in scen for o in ('adaptive', 'fixed') for k in range(nt)]
save('end_to_end.json', dict(runs=run_parallel(tasks, a.jobs)), a.quick)
