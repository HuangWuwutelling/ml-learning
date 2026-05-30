"""
Indoor Formaldehyde Box Model — 室内甲醛箱式模型

dC/dt = E/V + lambda * C_out - (lambda + k) * C

Core idea: a room is a well-mixed "box" — mass in, mass out, mass remaining.

Scenarios:
  - Windows closed: lambda ~0.1-0.3
  - Windows open:  lambda ~1-10
  - Activated carbon: k ~0.05-0.1 (saturates after hours)
  - Manganese dioxide (MnO2) catalytic filter: k ~0.5-1.0 (sustained)
  - Air purifier: k ~0.5-2.0 (depends on CADR)
"""

import numpy as np


class IndoorFormaldehyde:
    """Indoor formaldehyde concentration model — well-mixed box model.

    Parameters (all have sensible defaults for a typical bedroom):
        V      : room volume (m3), default 56 (20 m2 x 2.8 m)
        E      : emission rate (mg/h), default 5 (new furniture)
        C_out  : outdoor background (mg/m3), default 0.01
        lam    : air exchange rate (1/h), default 0.3 (closed windows)
        k      : removal rate from sorbent/catalyst (1/h), default 0
        C0     : initial indoor concentration (mg/m3), default 0
        label  : optional label for plotting
    """
    def __init__(self, V=56, E=5, C_out=0.01, lam=0.3, k=0, C0=0, label=''):
        self.V = V
        self.E = E
        self.C_out = C_out
        self.lam = lam
        self.k = k
        self.C0 = C0
        self.label = label

    # ── derived source/removal rates ──────────────────────────────
    @property
    def a(self):       # source term (mg/m3/h)
        return self.E / self.V + self.lam * self.C_out

    @property
    def b(self):       # removal term (1/h)
        return self.lam + self.k

    @property
    def C_ss(self):    # steady-state concentration (mg/m3)
        return self.a / self.b if self.b > 0 else np.inf

    # ── analytical solution ───────────────────────────────────────
    def concentration(self, t):
        """C(t) at elapsed time t (hours), using analytical solution of 1st-order linear ODE.

        C(t) = C0 * exp(-b*t) + (a/b) * (1 - exp(-b*t))
        """
        if self.b == 0:
            return self.C0 + self.a * t   # no removal => linear accumulation
        return self.C0 * np.exp(-self.b * t) + self.C_ss * (1 - np.exp(-self.b * t))

    def simulate(self, total_time, n_steps=2000):
        """Return (t_array, C_array) over [0, total_time] hours."""
        t = np.linspace(0, total_time, n_steps)
        return t, self.concentration(t)

    # ── numerical for time-varying parameters ─────────────────────
    def simulate_piecewise(self, segments, dt=0.01, C0=None):
        """Simulate with time-dependent parameters.

        segments: list of dicts, each with:
            {'E':..., 'lam':..., 'k':..., 'duration':hours}
            Omitted keys inherit previous value (or constructor default).

        Returns (t, C) where t is cumulative time.
        """
        t_segments = []
        C_segments = []
        C = self.C0 if C0 is None else C0
        t_elapsed = 0
        params = dict(E=self.E, lam=self.lam, k=self.k)

        for seg in segments:
            params.update({k: v for k, v in seg.items() if k != 'duration'})
            dur = seg['duration']
            lam, k, E = params['lam'], params['k'], params['E']
            a = E / self.V + lam * self.C_out
            b = lam + k

            n = int(dur / dt)
            t_local = np.linspace(0, dur, n, endpoint=False)
            if b == 0:
                C_local = C + a * t_local
            else:
                C_ss_local = a / b
                C_local = C * np.exp(-b * t_local) + C_ss_local * (1 - np.exp(-b * t_local))

            t_segments.append(t_elapsed + t_local)
            C_segments.append(C_local)
            C = C_local[-1]
            t_elapsed += dur

        return np.concatenate(t_segments), np.concatenate(C_segments)

    # ── long-term with emission decay ────────────────────────────
    @staticmethod
    def _E_decay(t_days, E0, alpha, E_inf=0.5):
        """Emission decays exponentially: E(t_days) = E_inf + E0 * exp(-alpha * t_days).
        t_days in days, alpha in per-day."""
        return E_inf + (E0 - E_inf) * np.exp(-alpha * t_days)

    def simulate_long_term(self, total_days, E0=None, alpha=0.02, E_inf=0.5,
                           dt=0.5, lam=None, k=None):
        """Long-term simulation (months) with decaying emission source.

        E(t) = E_inf + (E0 - E_inf) * exp(-alpha * t)

        The emission from new furniture decays as free formaldehyde is depleted.
        alpha ~0.01-0.03 per day for wood-based panels.
        """
        E0 = self.E if E0 is None else E0
        lam = self.lam if lam is None else lam
        k_val = self.k if k is None else k

        hours = total_days * 24
        n = int(hours / dt)
        t_hours = np.linspace(0, hours, n)
        C = np.empty(n)
        C[0] = self.C0

        for i in range(1, n):
            t_days = t_hours[i] / 24  # convert to days for E_decay
            E_t = self._E_decay(t_days, E0, alpha, E_inf)
            a = E_t / self.V + lam * self.C_out
            b = lam + k_val
            # analytical step (exact for constant a,b; E changes slowly over dt)
            if b == 0:
                C[i] = C[i - 1] + a * dt
            else:
                C[i] = C[i - 1] * np.exp(-b * dt) + (a / b) * (1 - np.exp(-b * dt))

        return t_hours / 24, C   # return in days

    # ── time to reach target concentration ────────────────────────
    def time_to_target(self, C_target, C0=None):
        """Hours to reach target concentration (analytical inverse).

        Handles both concentration-rising (C0 < C_ss) and falling (C0 > C_ss).
        Returns inf if target is unreachable in the current direction.
        """
        C0 = self.C0 if C0 is None else C0
        if self.b == 0:
            if abs(self.a) < 1e-15:
                return np.inf
            if self.a > 0 and C_target > C0:
                return (C_target - C0) / self.a
            if self.a < 0 and C_target < C0:
                return (C0 - C_target) / abs(self.a)
            return np.inf

        if abs(C0 - self.C_ss) < 1e-12:     # already at steady state
            return np.inf
        if C0 < self.C_ss:                   # rising toward C_ss
            if C_target <= C0 or C_target >= self.C_ss:
                return np.inf
            return -np.log((self.C_ss - C_target) / (self.C_ss - C0)) / self.b
        else:                                # falling toward C_ss
            if C_target >= C0 or C_target <= self.C_ss:
                return np.inf
            return -np.log((C_target - self.C_ss) / (C0 - self.C_ss)) / self.b


# ── Pre-built scenarios (for a typical 20 m2 bedroom) ──────────────

ROOM = dict(V=56, E=5, C_out=0.01)

SCENARIOS = {
    '关窗睡觉': IndoorFormaldehyde(**ROOM, lam=0.2, k=0, C0=0.05,
                    label='关窗睡觉 (λ=0.2)'),
    '开窗通风': IndoorFormaldehyde(**ROOM, lam=3.0, k=0, C0=0.05,
                    label='开窗通风 (λ=3.0)'),
    '活性炭包': IndoorFormaldehyde(**ROOM, lam=0.3, k=0.08, C0=0.05,
                    label='活性炭包 (k=0.08)'),
    '活性锰毡': IndoorFormaldehyde(**ROOM, lam=0.5, k=0.8, C0=0.05,
                    label='活性锰毡 (k=0.8)'),
    '开窗+活性锰': IndoorFormaldehyde(**ROOM, lam=2.0, k=0.8, C0=0.05,
                    label='开窗通风+活性锰毡'),
    '紧闭门窗': IndoorFormaldehyde(**ROOM, lam=0.1, k=0, C0=0.05,
                    label='紧闭门窗 (λ=0.1)'),
    '空气净化器': IndoorFormaldehyde(**ROOM, lam=0.3, k=1.5, C0=0.05,
                    label='空气净化器 (k=1.5, CADR=80)'),
}

# National standard
GB_STANDARD = 0.08   # mg/m3  GB/T 18883-2022


if __name__ == '__main__':
    # Quick smoke test
    m = IndoorFormaldehyde(V=56, E=5, C_out=0.01, lam=0.3, k=0)
    t, C = m.simulate(24)
    print(f'Steady state: {m.C_ss:.4f} mg/m3')
    print(f'After 24 h:   {C[-1]:.4f} mg/m3')
    print(f'OK:  IndoorFormaldehyde model works.')
