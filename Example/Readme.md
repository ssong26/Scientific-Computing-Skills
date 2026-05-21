# Subsurface Parallel Crack SIF Solver

This repository contains a Python implementation for the mixed-mode stress intensity factors of a pressurized crack parallel to a free surface in an elastic half-plane.

The problem originates from the classical dual-integral-equation formulation developed by Itou (1994) for a subsurface crack under internal pressure.

The main input is the normalized crack depth:

$$h/a$$

The main outputs are the normalized stress intensity factors:

$$K_I/(p\sqrt{\pi a})$$

$$K_{II}/(p\sqrt{\pi a})$$

where:

- $begin:math:text$a$end:math:text$ is the half crack length,
- $begin:math:text$h$end:math:text$ is the ligament thickness,
- $begin:math:text$p$end:math:text$ is the internal pressure.

Young's modulus does not appear in the normalized solution. Poisson's ratio $begin:math:text$ \\nu $end:math:text$ is retained as an input parameter.

---

# Physical Problem

We consider a crack of length $begin:math:text$2a$end:math:text$ located at depth $begin:math:text$h$end:math:text$ below a traction-free surface.

The crack is subjected to uniform internal pressure.

Because the crack is close to the free surface, the elastic field becomes strongly mixed-mode:

- mode I opening,
- mode II shear coupling,
- free-surface interaction,
- thin-ligament amplification.

The original analytical solution is expressed through coupled dual integral equations involving Fourier-Bessel kernels.

---

# Background

The original paper provides the dual-integral-equation structure, but many intermediate derivation steps are omitted, especially:

- Fourier-domain operator construction,
- compliance/stiffness mapping,
- sign conventions,
- asymptotic kernel behavior,
- numerical stabilization details.

This repository reconstructs the missing operator chain numerically and verifies it through:

- asymptotic consistency,
- kernel recovery,
- residual checks,
- convergence sweeps,
- and comparison against published benchmark values.

The crack opening expansions are written as:

$$\Delta V(x)=\frac{1}{\pi}\sum_{n=1}^{N}c_n\cos\left[(2n-1)\sin^{-1}(x/a)\right]$$

$$\Delta U(x)=\frac{1}{\pi}\sum_{n=1}^{N}d_n\sin\left[2n\sin^{-1}(x/a)\right]$$

whose Fourier transforms generate the Bessel-function structure:

$$J_{2n-1}(a\xi)$$

$$J_{2n}(a\xi)$$

used in the dual integral equations.

The implementation reconstructs the Fourier-domain kernels:

$$q_1(\xi),\ q_2(\xi),\ q_3(\xi),\ q_4(\xi)$$

through operator matching and asymptotic verification.

---

# Files

## `parallel_crack_sif_fast.py`

Fast single-run solver.

Purpose:

- quickly compute $begin:math:text$K\_I$end:math:text$ and $begin:math:text$K\_\{II\}$end:math:text$,
- suitable for parameter scans,
- minimal diagnostics.

Typical runtime:

- a few seconds.

---

## `parallel_crack_sif_verified.py`

Self-verifying research-grade solver.

Additional features:

- convergence sweep,
- weighted residual checks,
- near-tip verification,
- condition-number monitoring,
- kernel asymptotic checks,
- thin-layer failure detection.

This version is recommended for:

- publication-quality calculations,
- small $begin:math:text$h\/a$end:math:text$,
- numerical validation,
- and debugging.

Typical runtime:

- tens of seconds to minutes.

---

# Numerical Method

The implementation uses:

- Fourier-domain elasticity operators,
- weighted Galerkin / Schmidt projection,
- QR stabilization,
- asymptotic kernel subtraction,
- oscillatory quadrature,
- residual-based verification.

The large-$begin:math:text$\\xi$end:math:text$ asymptotic behavior is explicitly subtracted:

$$q_1/\xi \to -1/4$$

$$q_4/\xi \to -1/4$$

$$q_2/\xi \to 0$$

$$q_3/\xi \to 0$$

which significantly improves convergence of the oscillatory integrals.

---

# Installation

```bash
pip install numpy scipy
```

---

# Quick Usage

Fast version:

```bash
python parallel_crack_sif_fast.py --h_over_a 0.1
```

Verified version:

```bash
python parallel_crack_sif_verified.py --h_over_a 0.1
```

Example output:

```text
KI /(p*sqrt(pi*a))  ≈ 14.00
KII/(p*sqrt(pi*a)) ≈  8.81
```

---

# Verification

For the benchmark case:

$$h/a=0.1,\quad \nu=0.3$$

the computed values agree closely with the published Itou tables.

The verified solver additionally reports:

- weighted residual norms,
- off-grid boundary-condition errors,
- near-tip errors,
- matrix condition numbers,
- and convergence with basis order.

---

# Reliability and Thin-Layer Warning

The current basis performs well for moderate depth ratios such as:

$$h/a \gtrsim 0.05$$

For very small ligament thicknesses:

$$h/a \ll 0.05$$

the system becomes increasingly ill-conditioned because the upper layer behaves more like a thin plate or beam.

The verified solver automatically detects potential failure through:

- exploding condition numbers,
- unstable convergence,
- large residuals,
- and inconsistent SIF sweeps.

In that regime, a dedicated thin-layer asymptotic basis is recommended.

---

# Repository Structure

```text
README.md
derivation.md
parallel_crack_sif_fast.py
parallel_crack_sif_verified.py
```

- `README.md`:
  overview and usage.

- `derivation.md`:
  derivation audit trail and operator reconstruction.

- `parallel_crack_sif_fast.py`:
  production-style quick solver.

- `parallel_crack_sif_verified.py`:
  self-verifying research solver.

---

# Reference

```bibtex
@article{itou1994stress,
  title={Stress intensity factors around a crack parallel to a free surface of a half-plane},
  author={Itou, Shouetsu},
  journal={International Journal of Fracture},
  volume={67},
  number={2},
  pages={179--185},
  year={1994},
  publisher={Springer}
}
```

---

# Acknowledgment

The numerical implementation and repository structure were generated with assistance from ChatGPT.

The symbolic derivation chain and operator reconstruction workflow were iteratively developed through interaction with Gemini 2.5 Pro / Gemini Advanced reasoning models.

The final implementation was validated through:

- asymptotic checks,
- kernel reconstruction,
- residual verification,
- convergence sweeps,
- and benchmark comparison against the original reference.
