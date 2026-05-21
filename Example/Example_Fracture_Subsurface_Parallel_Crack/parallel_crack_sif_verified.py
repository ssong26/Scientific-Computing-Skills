"""
parallel_crack_sif_verified.py

Verified Schmidt/Galerkin-style solver for a pressurized crack parallel to a free
surface in an elastic half-plane, following the dual-integral-equation structure
of Itou (1994).

Inputs:
    h_over_a : crack depth / half crack length, h/a
    nu       : Poisson ratio, default 0.3

Outputs:
    KI_norm  = KI  / (p*sqrt(pi*a))
    KII_norm = KII / (p*sqrt(pi*a))

The Young's modulus is not needed for the dimensionless SIFs reported here.  The
internal kernel normalization is chosen to match Itou's convention, where
q1/xi -> -1/4 and q4/xi -> -1/4 at large xi.

Dependencies: numpy, scipy
"""
from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import quad
from scipy.special import jv


# -----------------------------------------------------------------------------
# Fourier-domain kernel q1, q2, q3, q4
# -----------------------------------------------------------------------------


def kappa_plane_stress(nu: float) -> float:
    return (3.0 - nu) / (1.0 + nu)


def _itou_mu(kappa: float) -> float:
    """Itou normalization: full-plane limit q1/xi=q4/xi=-1/4."""
    return (kappa + 1.0) / 8.0


def _region1_values(xi: float, y: float, kappa: float, mu: float, amps: np.ndarray):
    """u, v, sigma_xy, sigma_yy in finite layer -h<=y<=0."""
    A, B, C, D = amps
    k = abs(float(xi))
    if k == 0:
        k = 1e-14
    sg = 1.0 if xi >= 0 else -1.0
    ep = np.exp(k * y)
    em = np.exp(-k * y)
    u = (A + B * y) * ep + (C + D * y) * em
    v = 1j * sg * ((A - kappa * B / k + B * y) * ep - (C + kappa * D / k + D * y) * em)
    syy = 1j * sg * mu * (
        (2 * k * A - (kappa + 1) * B + 2 * k * B * y) * ep
        + (2 * k * C + (kappa + 1) * D + 2 * k * D * y) * em
    )
    sxy = mu * (
        (2 * k * A + (1 - kappa) * B + 2 * k * B * y) * ep
        + (-2 * k * C + (1 - kappa) * D - 2 * k * D * y) * em
    )
    return u, v, sxy, syy


def _region2_values(xi: float, y: float, kappa: float, mu: float, amps: np.ndarray):
    """u, v, sigma_xy, sigma_yy in lower half-plane y<=-h."""
    A, B = amps
    k = abs(float(xi))
    if k == 0:
        k = 1e-14
    sg = 1.0 if xi >= 0 else -1.0
    ep = np.exp(k * y)
    u = (A + B * y) * ep
    v = 1j * sg * (A - kappa * B / k + B * y) * ep
    syy = 1j * sg * mu * (2 * k * A - (kappa + 1) * B + 2 * k * B * y) * ep
    sxy = mu * (2 * k * A + (1 - kappa) * B + 2 * k * B * y) * ep
    return u, v, sxy, syy


def K_stress_numeric(xi: float, h: float, nu: float = 0.3) -> np.ndarray:
    """
    Stress stiffness matrix K for one Fourier wavenumber xi.

        [sigma_xy^1]   [K11 K12] [DeltaU_hat]
        [sigma_yy^1] = [K21 K22] [DeltaV_hat]

    Boundary conditions:
      sigma_xy1(y=0)=0, sigma_yy1(y=0)=0,
      u1(-h)-u2(-h)=DeltaU, v1(-h)-v2(-h)=DeltaV,
      sigma_xy1(-h)=sigma_xy2(-h), sigma_yy1(-h)=sigma_yy2(-h).
    """
    if h <= 0:
        raise ValueError("h must be positive")
    if abs(xi) < 1e-14:
        xi = 1e-14
    kappa = kappa_plane_stress(nu)
    mu = _itou_mu(kappa)

    A_mat = np.zeros((6, 6), dtype=complex)
    for j in range(6):
        basis = np.zeros(6, dtype=complex)
        basis[j] = 1.0
        r1 = basis[:4]
        r2 = basis[4:]
        _, _, sxy10, syy10 = _region1_values(xi, 0.0, kappa, mu, r1)
        u1h, v1h, sxy1h, syy1h = _region1_values(xi, -h, kappa, mu, r1)
        u2h, v2h, sxy2h, syy2h = _region2_values(xi, -h, kappa, mu, r2)
        A_mat[:, j] = [sxy10, syy10, u1h - u2h, v1h - v2h, sxy1h - sxy2h, syy1h - syy2h]

    K = np.zeros((2, 2), dtype=complex)
    for col, (dU, dV) in enumerate([(1.0, 0.0), (0.0, 1.0)]):
        rhs = np.array([0.0, 0.0, dU, dV, 0.0, 0.0], dtype=complex)
        sol = np.linalg.solve(A_mat, rhs)
        _, _, sxy1h, syy1h = _region1_values(xi, -h, kappa, mu, sol[:4])
        K[:, col] = [sxy1h, syy1h]
    return K


def q_values(xi: float, h: float, nu: float = 0.3) -> np.ndarray:
    """Return q1,q2,q3,q4 in Itou/stress-component convention."""
    K = K_stress_numeric(xi, h, nu=nu)
    q = np.array([K[1, 1], 1j * K[1, 0], -1j * K[0, 1], K[0, 0]], dtype=complex)
    return np.real_if_close(q, tol=1000).astype(float)


class KernelCache:
    def __init__(self, h: float, nu: float):
        self.h = float(h)
        self.nu = float(nu)

    @lru_cache(maxsize=300_000)
    def q_tuple(self, xi_rounded: float):
        return tuple(q_values(xi_rounded, self.h, self.nu).tolist())

    def q(self, xi: float) -> np.ndarray:
        return np.asarray(self.q_tuple(float(np.round(xi, 11))), dtype=float)


def validate_kernel_table(h_over_a: float = 0.1, nu: float = 0.3, a: float = 1.0) -> None:
    """Print values comparable to Itou Table 1 for h/a=0.1, nu=0.3."""
    h = h_over_a * a
    print(f"Kernel diagnostic: h/a={h_over_a}, nu={nu}")
    print("xi*a        q1/(xi*a)          q2/(xi*a)          q3/(xi*a)          q4/(xi*a)")
    for xa in [0.01, 0.21, 0.41, 74.41, 74.61, 74.81, 149.21, 149.41, 149.61]:
        q = q_values(xa / a, h, nu=nu)
        vals = q / xa
        print(f"{xa:8.2f}  {vals[0]: .8e}  {vals[1]: .8e}  {vals[2]: .8e}  {vals[3]: .8e}")


# -----------------------------------------------------------------------------
# Integral-equation solver
# -----------------------------------------------------------------------------


def default_asymptotes():
    # Q_i = q_i/xi ~ qL_i + q0_i/xi.  Itou-normalized high-frequency limit.
    return np.array([-0.25, 0.0, 0.0, -0.25], dtype=float), np.zeros(4, dtype=float)


def _subtracted_integral(q_index: int, order: int, osc: str, x: float, a: float, kernel: KernelCache,
                         xi_max: float, qL: np.ndarray, q0: np.ndarray,
                         epsabs: float, epsrel: float) -> float:
    trig = np.cos if osc == "cos" else np.sin
    qLi = qL[q_index]
    q0i = q0[q_index]

    def f(xi: float) -> float:
        if xi == 0.0:
            xi = 1e-12
        qi = kernel.q(xi)[q_index]
        Q = qi / xi
        return float((Q - qLi - q0i / xi) * jv(order, a * xi) * trig(xi * x))

    # Split the oscillatory integral into wavelength-scale windows.
    window = np.pi / max(a + abs(x), 1e-15)
    nwin = max(1, int(np.ceil(xi_max / window)))
    total = 0.0
    for kk in range(nwin):
        lo = kk * window
        hi = min((kk + 1) * window, xi_max)
        val, _ = quad(f, lo, hi, epsabs=epsabs, epsrel=epsrel, limit=100)
        total += val
    return total


def _entry_subtracted(q_index: int, order: int, osc: str, x: float, a: float, kernel: KernelCache,
                      xi_max: float, qL: np.ndarray, q0: np.ndarray,
                      epsabs: float, epsrel: float) -> float:
    """Integral ∫_0∞ [q_i(xi)/xi] J_order(a xi) cos/sin(xi x) dxi."""
    I = _subtracted_integral(q_index, order, osc, x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
    root = np.sqrt(max(a * a - x * x, 1e-300))
    theta = np.arcsin(np.clip(x / a, -1.0, 1.0))
    phi = np.cos(order * theta) if osc == "cos" else np.sin(order * theta)
    I += qL[q_index] * phi / root
    if order != 0:
        I += q0[q_index] * phi / order
    return float(I)


def gauss_points_on_crack(a: float, n_quad: int):
    t, w = leggauss(n_quad)
    x = 0.5 * a * (t + 1.0)
    wx = 0.5 * a * w
    return x, wx


def build_system(a: float, h_over_a: float, nu: float, p: float, n_terms: int, n_quad: int,
                 weight_power: float, xi_max_factor: float, epsabs: float, epsrel: float):
    h = h_over_a * a
    kernel = KernelCache(h=h, nu=nu)
    xs, ws = gauss_points_on_crack(a, n_quad)
    A = np.zeros((2 * n_quad, 2 * n_terms), dtype=float)
    b = np.zeros(2 * n_quad, dtype=float)
    xi_max = xi_max_factor / a
    qL, q0 = default_asymptotes()
    for j, x in enumerate(xs):
        rn = 2 * j
        rt = 2 * j + 1
        b[rn] = -p
        b[rt] = 0.0
        for n in range(1, n_terms + 1):
            mo = 2 * n - 1
            me = 2 * n
            I1 = _entry_subtracted(0, mo, "cos", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I2 = _entry_subtracted(1, me, "cos", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I3 = _entry_subtracted(2, mo, "sin", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I4 = _entry_subtracted(3, me, "sin", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            A[rn, n - 1] = (mo / np.pi) * I1
            A[rn, n_terms + n - 1] = (me / np.pi) * I2
            A[rt, n - 1] = (mo / np.pi) * I3
            A[rt, n_terms + n - 1] = (me / np.pi) * I4
    r = np.clip(xs / a, 0.0, 1.0)
    point_weights = np.sqrt(ws) * np.power(np.maximum(1.0 - r, 1e-15), weight_power)
    row_weights = np.repeat(point_weights, 2)
    Aw = A * row_weights[:, None]
    bw = b * row_weights
    return A, b, xs, ws, Aw, bw, row_weights


def modified_gram_schmidt_lstsq(A: np.ndarray, b: np.ndarray, rtol: float = 1e-12):
    m, n = A.shape
    Q = np.zeros((m, n), dtype=float)
    R = np.zeros((n, n), dtype=float)
    scale = max(float(np.max(np.linalg.norm(A, axis=0))), 1.0)
    rank = 0
    for j in range(n):
        v = A[:, j].copy()
        for i in range(rank):
            R[i, j] = np.dot(Q[:, i], v)
            v -= R[i, j] * Q[:, i]
        rjj = np.linalg.norm(v)
        if rjj <= rtol * scale:
            continue
        R[rank, j] = rjj
        Q[:, rank] = v / rjj
        rank += 1
    if rank == n:
        y = Q[:, :rank].T @ b
        x = np.linalg.solve(R[:rank, :], y)
    else:
        y = Q[:, :rank].T @ b
        x, *_ = np.linalg.lstsq(R[:rank, :], y, rcond=None)
    return x, rank


@dataclass
class SIFResult:
    h_over_a: float
    nu: float
    p: float
    a: float
    n_terms: int
    n_quad: int
    weight_power: float
    KI_norm: float
    KII_norm: float
    coeff_c: np.ndarray
    coeff_d: np.ndarray
    raw_residual: float
    weighted_residual: float
    cond: float
    rank: int
    mid_rms_normal: float | None = None
    mid_rms_shear: float | None = None
    tip_rms_normal: float | None = None
    tip_rms_shear: float | None = None
    mid_max_normal: float | None = None
    mid_max_shear: float | None = None
    tip_max_normal: float | None = None
    tip_max_shear: float | None = None


def sif_from_coefficients(c: np.ndarray, d: np.ndarray, p: float) -> tuple[float, float]:
    n = np.arange(1, len(c) + 1, dtype=float)
    qL = -0.25
    signs = (-1.0) ** n
    raw_KI = np.sum(c * (2 * n - 1) * signs * qL) / max(p, 1e-300)
    raw_KII = np.sum(d * (2 * n) * signs * qL) / max(p, 1e-300)
    return float(raw_KI / np.pi), float(-raw_KII / np.pi)


def evaluate_boundary(a: float, h_over_a: float, nu: float, p: float, coeff_c: np.ndarray, coeff_d: np.ndarray,
                      xs: np.ndarray, xi_max_factor: float, epsabs: float, epsrel: float):
    n_terms = len(coeff_c)
    kernel = KernelCache(h=h_over_a * a, nu=nu)
    qL, q0 = default_asymptotes()
    xi_max = xi_max_factor / a
    sig_yy = np.zeros_like(xs, dtype=float)
    sig_xy = np.zeros_like(xs, dtype=float)
    for j, x in enumerate(xs):
        nsum = 0.0
        tsum = 0.0
        for n in range(1, n_terms + 1):
            mo = 2 * n - 1
            me = 2 * n
            I1 = _entry_subtracted(0, mo, "cos", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I2 = _entry_subtracted(1, me, "cos", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I3 = _entry_subtracted(2, mo, "sin", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            I4 = _entry_subtracted(3, me, "sin", x, a, kernel, xi_max, qL, q0, epsabs, epsrel)
            nsum += coeff_c[n - 1] * (mo / np.pi) * I1 + coeff_d[n - 1] * (me / np.pi) * I2
            tsum += coeff_c[n - 1] * (mo / np.pi) * I3 + coeff_d[n - 1] * (me / np.pi) * I4
        sig_yy[j] = nsum
        sig_xy[j] = tsum
    return sig_yy, sig_xy


def solve_sif(h_over_a: float, nu: float = 0.3, p: float = 1.0, a: float = 1.0,
              n_terms: int = 14, n_quad: int = 60, weight_power: float = 0.5,
              xi_max_factor: float = 160.0, epsabs: float = 1e-7, epsrel: float = 1e-6,
              check: bool = True) -> SIFResult:
    A, b, xs, ws, Aw, bw, row_weights = build_system(
        a=a, h_over_a=h_over_a, nu=nu, p=p, n_terms=n_terms, n_quad=n_quad,
        weight_power=weight_power, xi_max_factor=xi_max_factor, epsabs=epsabs, epsrel=epsrel
    )
    sol, rank = modified_gram_schmidt_lstsq(Aw, bw)
    c = sol[:n_terms]
    d = sol[n_terms:]
    KI, KII = sif_from_coefficients(c, d, p)
    raw_rel = float(np.linalg.norm(A @ sol - b) / max(np.linalg.norm(b), 1e-15))
    w_rel = float(np.linalg.norm(Aw @ sol - bw) / max(np.linalg.norm(bw), 1e-15))
    res = SIFResult(
        h_over_a=h_over_a, nu=nu, p=p, a=a, n_terms=n_terms, n_quad=n_quad,
        weight_power=weight_power, KI_norm=KI, KII_norm=KII, coeff_c=c, coeff_d=d,
        raw_residual=raw_rel, weighted_residual=w_rel, cond=float(np.linalg.cond(Aw)), rank=rank
    )
    if check:
        for prefix, lo, hi in [("mid", 0.02, 0.80), ("tip", 0.80, 0.95)]:
            xcheck = a * np.linspace(lo, hi, 13)
            yy, xy = evaluate_boundary(a, h_over_a, nu, p, c, d, xcheck, xi_max_factor, epsabs, epsrel)
            en = yy + p
            et = xy
            setattr(res, f"{prefix}_rms_normal", float(np.sqrt(np.mean(en * en))))
            setattr(res, f"{prefix}_rms_shear", float(np.sqrt(np.mean(et * et))))
            setattr(res, f"{prefix}_max_normal", float(np.max(np.abs(en))))
            setattr(res, f"{prefix}_max_shear", float(np.max(np.abs(et))))
    return res


def trust_flag(results: list[SIFResult]) -> tuple[str, str]:
    """Classify reliability from N-convergence, residual, and condition number."""
    r_hi = results[-1]
    if len(results) >= 2:
        r_lo = results[-2]
        dKI = abs(r_hi.KI_norm - r_lo.KI_norm) / max(abs(r_hi.KI_norm), 1e-15)
        dKII = abs(r_hi.KII_norm - r_lo.KII_norm) / max(abs(r_hi.KII_norm), 1e-15)
        dmax = max(dKI, dKII)
    else:
        dmax = np.inf
    resid = max(r_hi.weighted_residual, r_hi.mid_rms_normal or 0.0, r_hi.mid_rms_shear or 0.0)
    tip = max(r_hi.tip_rms_normal or 0.0, r_hi.tip_rms_shear or 0.0)
    cond = r_hi.cond
    if dmax < 0.01 and resid < 1e-2 and tip < 5e-2 and cond < 1e5:
        return "reliable", f"N-convergence={dmax:.2%}, residual={resid:.2e}, tip={tip:.2e}, cond={cond:.2e}"
    if dmax < 0.05 and resid < 1e-1 and cond < 5e5:
        return "warning", f"N-convergence={dmax:.2%}, residual={resid:.2e}, tip={tip:.2e}, cond={cond:.2e}"
    return "failed", f"N-convergence={dmax:.2%}, residual={resid:.2e}, tip={tip:.2e}, cond={cond:.2e}"


def solve_sif_verified(h_over_a: float, nu: float = 0.3, p: float = 1.0, a: float = 1.0,
                       n_values: Iterable[int] = (10, 12, 14), n_quad: int = 60,
                       weight_power: float = 0.5, xi_max_factor: float = 160.0,
                       epsabs: float = 1e-7, epsrel: float = 1e-6) -> tuple[list[SIFResult], str, str]:
    out: list[SIFResult] = []
    for N in n_values:
        t0 = time.time()
        r = solve_sif(h_over_a, nu=nu, p=p, a=a, n_terms=N, n_quad=n_quad,
                      weight_power=weight_power, xi_max_factor=xi_max_factor,
                      epsabs=epsabs, epsrel=epsrel, check=True)
        r.runtime = time.time() - t0  # type: ignore[attr-defined]
        out.append(r)
    flag, reason = trust_flag(out)
    return out, flag, reason


def print_one(res: SIFResult) -> None:
    print(f"h/a={res.h_over_a:g}, nu={res.nu:g}, N={res.n_terms}, n_quad={res.n_quad}, weight={res.weight_power:g}")
    print(f"KI /(p*sqrt(pi*a))  = {res.KI_norm:.10g}")
    print(f"KII/(p*sqrt(pi*a))  = {res.KII_norm:.10g}")
    print(f"weighted residual   = {res.weighted_residual:.3e}; raw residual={res.raw_residual:.3e}; cond={res.cond:.3e}")
    if res.mid_rms_normal is not None:
        print(f"mid RMS normal/shear = {res.mid_rms_normal:.3e}, {res.mid_rms_shear:.3e}")
        print(f"tip RMS normal/shear = {res.tip_rms_normal:.3e}, {res.tip_rms_shear:.3e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verified SIF solver for a subsurface crack parallel to a free surface.")
    parser.add_argument("--h_over_a", type=float, default=0.1)
    parser.add_argument("--nu", type=float, default=0.3)
    parser.add_argument("--p", type=float, default=1.0)
    parser.add_argument("--a", type=float, default=1.0)
    parser.add_argument("--n_values", type=str, default="10,12,14", help="Comma-separated N values for convergence check")
    parser.add_argument("--n_quad", type=int, default=60)
    parser.add_argument("--weight_power", type=float, default=0.5)
    parser.add_argument("--xi_max_factor", type=float, default=160.0)
    parser.add_argument("--epsabs", type=float, default=1e-7)
    parser.add_argument("--epsrel", type=float, default=1e-6)
    parser.add_argument("--save_csv", type=str, default="")
    parser.add_argument("--kernel_check", action="store_true")
    args = parser.parse_args()

    if args.kernel_check:
        validate_kernel_table(args.h_over_a, args.nu, args.a)
        return

    n_values = tuple(int(v.strip()) for v in args.n_values.split(",") if v.strip())
    results, flag, reason = solve_sif_verified(
        args.h_over_a, nu=args.nu, p=args.p, a=args.a, n_values=n_values,
        n_quad=args.n_quad, weight_power=args.weight_power, xi_max_factor=args.xi_max_factor,
        epsabs=args.epsabs, epsrel=args.epsrel
    )
    print("Verified SIF solver")
    print(f"h/a={args.h_over_a:g}, nu={args.nu:g}; N values={n_values}")
    print("N        KI_norm        KII_norm       wrel       midN       midT       tipN       tipT       cond")
    for r in results:
        print(f"{r.n_terms:<3d} {r.KI_norm:14.8f} {r.KII_norm:14.8f} {r.weighted_residual:9.2e} "
              f"{r.mid_rms_normal:9.2e} {r.mid_rms_shear:9.2e} {r.tip_rms_normal:9.2e} {r.tip_rms_shear:9.2e} {r.cond:9.2e}")
    print(f"\nstatus: {flag}")
    print(f"reason: {reason}")
    print("\nRecommended result: highest-N row")
    print_one(results[-1])

    if args.save_csv:
        with open(args.save_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["h_over_a", "nu", "N", "n_quad", "weight_power", "KI_norm", "KII_norm", "wrel", "rawrel", "midN", "midT", "tipN", "tipT", "cond", "rank"])
            for r in results:
                w.writerow([r.h_over_a, r.nu, r.n_terms, r.n_quad, r.weight_power, r.KI_norm, r.KII_norm, r.weighted_residual, r.raw_residual, r.mid_rms_normal, r.mid_rms_shear, r.tip_rms_normal, r.tip_rms_shear, r.cond, r.rank])
        print(f"Saved CSV to {args.save_csv}")


if __name__ == "__main__":
    main()
