# Subsurface Parallel Crack SIF Solver

This repository contains a small Python implementation for the stress intensity factors of a pressurized crack parallel to a stress-free surface in an elastic half-plane.

The main inputs are the crack-depth ratio `h/a` and Poisson's ratio `nu`. The outputs are the dimensionless stress intensity factors

$$
K_I/(p\sqrt{\pi a}), \qquad K_{II}/(p\sqrt{\pi a}).
$$

Young's modulus is not required for these normalized quantities. Poisson's ratio is retained as an input, although the benchmark values are weakly sensitive to it.

---

# Files

- `parallel_crack_sif_fast.py`  
  Fast one-shot calculator for a single `h/a`.

- `parallel_crack_sif_verified.py`  
  Slower self-verifying solver. It runs multiple truncation orders, reports residuals, condition numbers, and a reliability flag.

---

# Background

The implementation follows the dual-integral-equation structure used by Itou (1994) for a crack parallel to a free surface. The omitted Fourier-domain kernel functions

$$
q_1(\xi), q_2(\xi), q_3(\xi), q_4(\xi)
$$

are reconstructed through operator matching and asymptotic consistency checks.

The crack opening jumps are expanded as

$$
\Delta V(x)=\frac{1}{\pi}\sum_{n=1}^{N} c_n
\cos\left[(2n-1)\sin^{-1}\left(\frac{x}{a}\right)\right],
$$

$$
\Delta U(x)=\frac{1}{\pi}\sum_{n=1}^{N} d_n
\sin\left[2n\sin^{-1}\left(\frac{x}{a}\right)\right].
$$

The finite Fourier transforms of these functions produce Bessel terms

$$
J_{2n-1}(a\xi), \qquad J_{2n}(a\xi),
$$

yielding the same dual integral equation structure as the original paper.

The numerical implementation includes:

- asymptotic kernel subtraction,
- weighted Galerkin/Schmidt projection,
- convergence diagnostics,
- residual verification,
- and thin-layer failure detection.

The high-frequency parts of the oscillatory integrals are subtracted analytically using the asymptotic behavior

$$
q_1/\xi \to -1/4,
\qquad
q_4/\xi \to -1/4,
$$

with

$$
q_2/\xi,\ q_3/\xi \to 0.
$$

---
# Reference 
@article{itou1994stress,
  title={Stress intensity factors around a crack parallel to a free surface of a half-plane},
  author={Itou, Shouetsu},
  journal={International journal of fracture},
  volume={67},
  number={2},
  pages={179--185},
  year={1994},
  publisher={Springer}
}
# Installation

```bash
pip install numpy scipy
