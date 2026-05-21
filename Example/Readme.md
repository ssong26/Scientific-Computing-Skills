# Subsurface Parallel Crack SIF Solver

This repository contains a small Python implementation for the stress intensity factors of a pressurized crack parallel to a stress-free surface in an elastic half-plane.

The main inputs are the crack-depth ratio `h/a` and Poisson's ratio `nu`. The outputs are the dimensionless stress intensity factors

\[
K_I/(p\sqrt{\pi a}), \qquad K_{II}/(p\sqrt{\pi a}).
\]

Young's modulus is not required for these normalized quantities. Poisson's ratio is retained as an input, although the benchmark values are weakly sensitive to it.

## Files

- `parallel_crack_sif_fast.py`  
  Fast one-shot calculator for a single `h/a`.

- `parallel_crack_sif_verified.py`  
  Slower self-verifying solver. It runs multiple truncation orders, reports residuals, condition numbers, and a reliability flag.

## Background

The implementation follows the dual-integral-equation structure used by Itou (1994) for a crack parallel to a free surface. The omitted kernel functions \(q_1,q_2,q_3,q_4\) are reconstructed numerically from the Fourier-domain traction-displacement operator.

The crack opening jumps are expanded as

\[
\Delta V(x)=\frac{1}{\pi}\sum_{n=1}^{N} c_n\cos\left[(2n-1)\sin^{-1}(x/a)\right],
\]

\[
\Delta U(x)=\frac{1}{\pi}\sum_{n=1}^{N} d_n\sin\left[2n\sin^{-1}(x/a)\right].
\]

The finite Fourier transforms of these functions produce Bessel terms \(J_{2n-1}(a\xi)\) and \(J_{2n}(a\xi)\), giving the same dual integral equation structure as the original paper.

The numerical solver uses a Schmidt/Galerkin-style weighted least-squares projection of the residual equations. The high-frequency parts of the oscillatory integrals are subtracted analytically, using the asymptotic behavior

\[
q_1/\xi \to -1/4, \qquad q_4/\xi \to -1/4,
\]

with \(q_2/\xi,q_3/\xi\to 0\).

## Installation

```bash
pip install numpy scipy
```

## Fast usage

```bash
python parallel_crack_sif_fast.py --h_over_a 0.1
```

Typical result for `h/a=0.1`, `nu=0.3`:

```text
KI /(p*sqrt(pi*a))  ≈ 14.006
KII/(p*sqrt(pi*a))  ≈  8.811
```

The original Itou table gives approximately

```text
KI  ≈ 13.9714
KII ≈  8.7847
```

The small difference is within the range expected from truncation and implementation differences. The present solver also reports residual diagnostics when checks are enabled.

## Verified usage

For a more reliable calculation, especially for small `h/a`, use:

```bash
python parallel_crack_sif_verified.py --h_over_a 0.1
```

This runs several truncation orders, by default:

```text
N = 10, 12, 14
```

and reports:

- `KI_norm`, `KII_norm`
- weighted residual
- mid-region residuals
- near-tip residuals
- matrix condition number
- reliability flag: `reliable`, `warning`, or `failed`

Example:

```bash
python parallel_crack_sif_verified.py --h_over_a 0.05 --n_values 10,12,14 --save_csv result.csv
```

## Kernel diagnostic

To check the reconstructed \(q_i\) kernels against the known Table-1 behavior for `h/a=0.1`, run:

```bash
python parallel_crack_sif_verified.py --kernel_check --h_over_a 0.1 --nu 0.3
```

The output should show

```text
q1/(xi*a) -> -0.25
q4/(xi*a) -> -0.25
q2/(xi*a), q3/(xi*a) -> 0
```

for large `xi*a`.

## Reliability for very small h/a

For `h/a < 0.05`, the current crack-opening basis may become poorly conditioned because the upper ligament behaves more like a thin beam or plate. In that regime, do not trust a single fast run. Use the verified solver and check:

1. convergence with increasing `N`,
2. weighted and off-grid residuals,
3. condition number,
4. stability of `KI` and `KII`.

If the verified solver returns `failed`, the current basis is not reliable for that depth ratio. A thin-layer/asymptotic-enriched basis is then recommended.

## Method summary

The workflow is:

1. Construct the Fourier-domain elasticity kernel for the layer plus lower half-plane.
2. Extract the dual-integral kernels \(q_1,q_2,q_3,q_4\).
3. Apply high-frequency subtraction for stable oscillatory quadrature.
4. Solve for the crack-opening coefficients \(c_n,d_n\) using a weighted Schmidt/Galerkin least-squares system.
5. Compute the normalized stress intensity factors from the high-frequency coefficient sums.
6. Verify by residual checks and convergence with respect to truncation order.

## Notes

This code is intended as a research/verification implementation rather than a black-box fracture mechanics package. The `verified` script is the recommended interface when reporting new values.
