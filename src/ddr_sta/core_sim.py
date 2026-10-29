"""
Plant + super-twisting observers + filtered RLS identification pipeline.

Plant: two brushed DC motors coupled through the chassis effective-inertia matrix
M = [[alpha, beta], [beta, alpha]] (see paper, Section II).
Observers: per-channel adaptive-gain super-twisting observer (the proposed design) and
a constant-gain observer (reference design that needs an a priori acceleration bound).
Identification: first-order-filtered regression with recursive least squares, theta = [alpha, beta, b].
"""
import numpy as np

# Known (bench-characterised) electrical parameters and geometry
R_a = 2.0        # armature resistance [Ohm]
L_a = 3.0e-3     # armature inductance [H]
K_b = 0.05       # back-EMF constant
K_t = 0.05       # torque constant
b_visc = 1.0e-4  # viscous friction
r = 0.033        # wheel radius [m]
d = 0.08         # track half-width parameter used in the paper's M matrix [m]


def build_M(m_, I_z_, J_w_):
    """Effective inertia matrix M and its entries (alpha, beta)."""
    alpha = J_w_ + m_ * r**2 / 4 + I_z_ * r**2 / (4 * d**2)
    beta = r**2 * (d**2 * m_ - I_z_) / (4 * d**2)
    return np.array([[alpha, beta], [beta, alpha]]), alpha, beta


def fixed_gains(delta_omega_dot=1398.0, w_ratio=2.0, margin=1.15):
    """Constant gains (kappa1, kappa2) from the sufficient condition
    W > L,  lambda^2 >= 4L(W+L)/(W-L), with L = (K_b/L_a) * delta_omega_dot.
    This design needs the true wheel-acceleration bound: it is only a reference."""
    L = (K_b / L_a) * delta_omega_dot
    W = w_ratio * L
    lam = margin * np.sqrt(4 * L * (W + L) / (W - L))
    return lam, W


class FixedSTA:
    """Constant-gain super-twisting current/speed observer (reference design)."""
    def __init__(self, kappa1, kappa2):
        self.ihat = 0.0
        self.z = 0.0
        self.k1 = kappa1
        self.k2 = kappa2

    def step(self, dt, i_meas, u):
        e = i_meas - self.ihat
        dihat = (-R_a * self.ihat + u) / L_a + self.z + self.k1 * np.sqrt(abs(e)) * np.sign(e)
        dz = self.k2 * np.sign(e)
        self.ihat += dt * dihat
        self.z += dt * dz
        return -(L_a / K_b) * self.z, e


class AdaptiveSTA:
    """Adaptive-gain super-twisting observer (the proposed design).
    kappa1 grows at rate `growth_rate` while |e| > eps and decays otherwise (floor kappa1_min);
    kappa2 = rho * kappa1. No plant parameter and no disturbance bound enters the gain law."""
    def __init__(self, kappa1_0=1.0, kappa1_min=1.0, growth_rate=2000.0, rho=88.0, eps=1e-4):
        self.ihat = 0.0
        self.z = 0.0
        self.kappa1 = kappa1_0
        self.kappa1_min = kappa1_min
        self.gamma = growth_rate
        self.rho = rho
        self.eps = eps

    def step(self, dt, i_meas, u):
        e = i_meas - self.ihat
        k2 = self.rho * self.kappa1
        dihat = (-R_a * self.ihat + u) / L_a + self.z + self.kappa1 * np.sqrt(abs(e)) * np.sign(e)
        dz = k2 * np.sign(e)
        if abs(e) > self.eps:
            dk1 = self.gamma
        else:
            dk1 = -self.gamma if self.kappa1 > self.kappa1_min else self.gamma
        self.ihat += dt * dihat
        self.z += dt * dz
        self.kappa1 = max(self.kappa1 + dt * dk1, self.kappa1_min)
        return -(L_a / K_b) * self.z, e


class LowPass:
    """First-order filter p/(s+p) in state-space form."""
    def __init__(self, p, x0=0.0):
        self.p = p
        self.xf = x0

    def step(self, dt, x):
        self.xf += dt * self.p * (x - self.xf)
        return self.xf


class RLS3:
    """Recursive least squares, no forgetting factor, P0 = I/delta, theta = [alpha, beta, b]."""
    def __init__(self, delta=1e-3):
        self.theta = np.zeros(3)
        self.P = np.eye(3) / delta

    def update(self, phi, y):
        Pphi = self.P @ phi
        denom = 1.0 + phi @ Pphi
        gain = Pphi / denom
        err = y - phi @ self.theta
        self.theta = self.theta + gain * err
        self.P = self.P - np.outer(gain, Pphi)
        return self.theta.copy()


def plant_step_rk4(x, t, dt, M, Minv, uR_fn, uL_fn, tauR_fn, tauL_fn):
    """One RK4 step of the coupled electromechanical plant, x = [iR, iL, wR, wL]."""
    def f(tt, xx):
        iR, iL, wR, wL = xx
        uR, uL = uR_fn(tt), uL_fn(tt)
        tauR, tauL = tauR_fn(tt), tauL_fn(tt)
        diR = (-R_a * iR - K_b * wR + uR) / L_a
        diL = (-R_a * iL - K_b * wL + uL) / L_a
        rhs_mech = np.array([K_t * iR, K_t * iL]) - b_visc * np.array([wR, wL]) - np.array([tauR, tauL])
        dw = Minv @ rhs_mech
        return np.array([diR, diL, dw[0], dw[1]])
    k1 = f(t, x)
    k2 = f(t + dt / 2, x + dt / 2 * k1)
    k3 = f(t + dt / 2, x + dt / 2 * k2)
    k4 = f(t + dt, x + dt * k3)
    return x + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


def run_pipeline(m_, I_z_, J_w_, uR_fn, uL_fn, tauR_fn, tauL_fn,
                 observer_type='adaptive', adapt_kwargs=None, fixed_kwargs=None,
                 T=4.0, dt=5e-5, filt_pole=1.0, rls_dt=1e-3, rls_delta=1e-3,
                 sigma_i=0.0, seed=0, warmup=1.5, x0=None):
    """plant -> observer -> low-pass filter -> RLS. Returns time series and final estimates."""
    rng = np.random.default_rng(seed)
    M, alpha_true, beta_true = build_M(m_, I_z_, J_w_)
    Minv = np.linalg.inv(M)

    n = int(T / dt)
    x = np.zeros(4) if x0 is None else np.array(x0, dtype=float)

    if observer_type == 'adaptive':
        ak = adapt_kwargs or dict(kappa1_0=1.0, kappa1_min=1.0, growth_rate=2000.0, rho=88.0, eps=1e-4)
        obsR, obsL = AdaptiveSTA(**ak), AdaptiveSTA(**ak)
    else:
        lam, W = fixed_gains()
        fk = fixed_kwargs or dict(kappa1=lam, kappa2=W)
        obsR, obsL = FixedSTA(**fk), FixedSTA(**fk)

    fwR, fwL = LowPass(filt_pole), LowPass(filt_pole)
    fiR, fiL = LowPass(filt_pole), LowPass(filt_pole)
    rls = RLS3(delta=rls_delta)
    rls_step = max(int(rls_dt / dt), 1)

    theta_hist, t_theta = [], []
    wR_true = np.empty(n); wL_true = np.empty(n)
    wR_hat = np.empty(n); wL_hat = np.empty(n)
    k1_hist = np.full(n, np.nan)
    t = 0.0

    for k in range(n):
        x = plant_step_rk4(x, t, dt, M, Minv, uR_fn, uL_fn, tauR_fn, tauL_fn)
        iR, iL, wR, wL = x
        uRn, uLn = uR_fn(t), uL_fn(t)

        iR_meas = iR + (rng.normal(0, sigma_i) if sigma_i > 0 else 0.0)
        iL_meas = iL + (rng.normal(0, sigma_i) if sigma_i > 0 else 0.0)

        wRh, _ = obsR.step(dt, iR_meas, uRn)
        wLh, _ = obsL.step(dt, iL_meas, uLn)
        if observer_type == 'adaptive':
            k1_hist[k] = obsR.kappa1

        wRf = fwR.step(dt, wRh); wLf = fwL.step(dt, wLh)
        iRf = fiR.step(dt, iR_meas); iLf = fiL.step(dt, iL_meas)

        if k % rls_step == 0 and t >= warmup:
            p = filt_pole
            phiR = np.array([p * (wRh - wRf), p * (wLh - wLf), wRf]); yR = K_t * iRf
            phiL = np.array([p * (wLh - wLf), p * (wRh - wRf), wLf]); yL = K_t * iLf
            rls.update(phiR, yR)
            th = rls.update(phiL, yL)
            theta_hist.append(th.copy())
            t_theta.append(t)

        wR_true[k], wL_true[k], wR_hat[k], wL_hat[k] = wR, wL, wRh, wLh
        t += dt

    theta_hist = np.array(theta_hist)
    mask = np.arange(n) * dt > warmup
    speed_scale = np.sqrt(np.mean(wR_true[mask]**2 + wL_true[mask]**2) / 2)
    obs_err = np.sqrt(np.mean((wR_true[mask] - wR_hat[mask])**2 + (wL_true[mask] - wL_hat[mask])**2) / 2)

    return dict(theta_hist=theta_hist, t_theta=np.array(t_theta),
                alpha_true=alpha_true, beta_true=beta_true, b_true=b_visc,
                theta_final=theta_hist[-1] if len(theta_hist) else np.full(3, np.nan),
                obs_rms_pct=100 * obs_err / speed_scale, speed_scale=speed_scale,
                wR_true=wR_true, wL_true=wL_true, wR_hat=wR_hat, wL_hat=wL_hat,
                k1R=k1_hist, rls_P=rls.P, rls_delta=rls_delta, dt=dt, warmup=warmup)
