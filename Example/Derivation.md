Here's the markdown with proper GitHub-friendly LaTeX (no `begin:math:text` placeholders, clean display/inline math, and no ambiguous line breaks inside math environments).

```markdown
# Derivation of the Dual-Integral Equation Solver for a Subsurface Parallel Crack

This note summarizes the derivation used in the numerical solver for a pressurized crack parallel to a stress-free surface in an elastic half-plane.

The derivation reconstructs the Fourier-domain kernel functions

$$
q_1(\xi),\ q_2(\xi),\ q_3(\xi),\ q_4(\xi)
$$

used in the dual-integral equations of Itou (1994).

The purpose of this document is not to reproduce the original paper line-by-line, but to provide a transparent derivation chain suitable for numerical implementation and auditing.

---

# 1. Geometry

We consider a crack of length

$$
2a
$$

located at depth

$$
h
$$

below a free surface.

The coordinate system is:

- free surface: $y=0$
- crack plane: $y=-h$

The crack occupies $|x| < a$.

The geometry is divided into two regions:

## Region 1: finite layer

$$
-h \le y \le 0
$$

## Region 2: lower half-space

$$
-\infty < y \le -h
$$

---

# 2. Boundary conditions

At the free surface:

$$
\sigma_{xy}^{(1)}(x,0)=0,\qquad \sigma_{yy}^{(1)}(x,0)=0.
$$

At the bonded interface outside the crack:

$$
u^{(1)}=u^{(2)},\qquad v^{(1)}=v^{(2)}.
$$

Inside the crack:

$$
\sigma_{yy}=-p,\qquad \sigma_{xy}=0.
$$

---

# 3. Fourier transform convention

Forward transform:

$$
\widehat{f}(\xi) = \int_{-\infty}^{\infty} f(x) e^{i\xi x} \, dx
$$

Inverse transform:

$$
f(x) = \frac{1}{2\pi} \int_{-\infty}^{\infty} \widehat{f}(\xi) e^{-i\xi x} \, d\xi
$$

Under this convention:

$$
\frac{\partial}{\partial x} \;\leftrightarrow\; -i\xi
$$

---

# 4. Full-plane calibration limit

Before solving the layered problem, the deep-interface limit $h\to\infty$ is used to calibrate signs and phases.

For an isolated crack plane in an infinite medium:

$$
\begin{bmatrix}
\widehat{\sigma}_{xy} \\
\widehat{\sigma}_{yy}
\end{bmatrix}
=
-\frac{2\mu|\xi|}{\kappa+1}
\mathbf{I}
\begin{bmatrix}
\widehat{\Delta U} \\
\widehat{\Delta V}
\end{bmatrix}
$$

with

$$
\kappa = \frac{3-\nu}{1+\nu}
$$

for plane stress. This provides the asymptotic reference kernel.

---

# 5. Crack-opening expansions

The displacement jumps are expanded as bounded basis functions which automatically vanish outside the crack interval.

## Normal opening

$$
\Delta V(x) = \frac{1}{\pi} \sum_{n=1}^{N} c_n \cos\left[(2n-1)\sin^{-1}(x/a)\right]
$$

This basis is even in $x$.

## Tangential opening

$$
\Delta U(x) = \frac{1}{\pi} \sum_{n=1}^{N} d_n \sin\left[2n\sin^{-1}(x/a)\right]
$$

This basis is odd in $x$.

---

# 6. Fourier transforms of the crack openings

Using $x = a\sin\theta$, $dx = a\cos\theta\, d\theta$, the Fourier transforms reduce to Bessel-function forms.

## Normal jump

$$
\widehat{\Delta V}(\xi) = \sum_{n=1}^{N} c_n \frac{2n-1}{\xi} J_{2n-1}(a\xi)
$$

## Tangential jump

$$
\widehat{\Delta U}(\xi) = i \sum_{n=1}^{N} d_n \frac{2n}{\xi} J_{2n}(a\xi)
$$

These are the key spectral representations used in the dual-integral equations.

---

# 7. Compliance operator

The interface relation is written as

$$
\begin{bmatrix}
\widehat{\Delta U} \\
\widehat{\Delta V}
\end{bmatrix}
=
\mathbf{C}
\begin{bmatrix}
\widehat{\sigma}_{xy} \\
\widehat{\sigma}_{yy}
\end{bmatrix}
$$

where

$$
\mathbf{C} = \mathbf{C}^{(1)} - \mathbf{C}^{(2)}
$$

is the difference between the finite-layer compliance and the lower half‑space compliance.

The stiffness matrix is then $\mathbf{K} = \mathbf{C}^{-1}$.

---

# 8. Fourier-domain traction kernels

The stiffness relation becomes

$$
\begin{bmatrix}
\widehat{\sigma}_{xy} \\
\widehat{\sigma}_{yy}
\end{bmatrix}
=
\mathbf{K}
\begin{bmatrix}
\widehat{\Delta U} \\
\widehat{\Delta V}
\end{bmatrix}
$$

with

$$
\mathbf{K} =
\begin{bmatrix}
K_{11} & K_{12} \\
K_{21} & K_{22}
\end{bmatrix}.
$$

Substituting the Bessel expansions produces the dual-integral structure.

---

# 9. Identification of $q_1$, $q_2$, $q_3$, $q_4$

Matching the resulting inverse Fourier integrals to the standard dual-integral form gives:

$$
q_1(\xi) = K_{22}(\xi),\qquad
q_2(\xi) = i K_{21}(\xi),\qquad
q_3(\xi) = -i K_{12}(\xi),\qquad
q_4(\xi) = K_{11}(\xi)
$$

for the stress‑component convention. If outward traction conventions are used instead, the overall signs reverse accordingly.

---

# 10. High-frequency asymptotics

The large‑$\xi$ asymptotics are essential for stable numerical quadrature.

The kernels satisfy:

$$
\frac{q_1}{\xi} \to -\frac14,\qquad
\frac{q_4}{\xi} \to -\frac14,
$$

while

$$
\frac{q_2}{\xi},\ \frac{q_3}{\xi} \to 0.
$$

These asymptotic pieces are subtracted analytically before numerical integration, which dramatically improves convergence.

---

# 11. Numerical method

The final numerical system is constructed using:

- weighted least squares,
- Schmidt/Galerkin projection,
- QR‑based stabilization,
- asymptotic subtraction,
- residual verification.

The unknowns are $c_n$ and $d_n$. Once solved, the stress intensity factors are extracted from the high‑frequency behavior of the coefficients.

---

# 12. Verification strategy

The implementation is verified using:

## 1. Published benchmark comparison

For example, $h/a = 0.1,\ \nu = 0.3$ compared against Itou’s published tables.

## 2. Residual verification

Boundary‑condition residuals are checked:

- inside the crack,
- near the crack tip,
- away from the tip.

## 3. Convergence with basis order

Solutions are checked for convergence as $N \to N+2$.

## 4. Kernel asymptotics

The numerical kernels must recover $q_1/\xi \to -1/4$ and $q_4/\xi \to -1/4$.

---

# 13. Thin-layer warning

For very small $h/a$ the current basis becomes increasingly ill‑conditioned because the upper ligament behaves more like a thin plate.

Indicators of failure include:

- exploding condition number,
- non‑convergent $K_I, K_{II}$,
- large weighted residuals,
- unstable near‑tip errors.

In that regime, an asymptotic thin‑layer basis should be introduced.

---

# 14. Repository philosophy

This repository is intended as:

- a derivation audit trail,
- a research‑grade verification implementation,
- and an example of AI‑assisted continuum‑mechanics reconstruction.

The derivation was developed iteratively through:

1. symbolic operator reconstruction,
2. asymptotic consistency checks,
3. numerical kernel verification,
4. and independent cross‑auditing of sign conventions and limits.

The final solver is therefore not a direct transcription of the original paper, but an independently reconstructed implementation constrained by all known consistency conditions.
```

Just copy this block into your `.md` file – GitHub will render the math correctly without “抽风” (weird rendering).
