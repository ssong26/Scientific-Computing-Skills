# Subsurface Parallel Crack: Derivation Notes

This document summarizes the derivation used in the numerical solver for a pressurized crack parallel to a free surface in an elastic half-plane.

The goal is to reconstruct the dual-integral kernels

$$
q_1(\xi),\ q_2(\xi),\ q_3(\xi),\ q_4(\xi)
$$

from Fourier-domain elasticity operators.

---

# 1. Geometry

We consider:

- free surface:
  
$$
y=0
$$

- crack plane:

$$
y=-h
$$

- crack interval:

$$
|x|<a
$$

The geometry is divided into two regions.

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
\sigma_{xy}^{(1)}(x,0)=0
$$

$$
\sigma_{yy}^{(1)}(x,0)=0
$$

Outside the crack:

$$
u^{(1)}=u^{(2)}
$$

$$
v^{(1)}=v^{(2)}
$$

Inside the crack:

$$
\sigma_{yy}=-p
$$

$$
\sigma_{xy}=0
$$

---

# 3. Fourier transform convention

Forward transform:

$$
\widehat{f}(\xi)
=
\int_{-\infty}^{\infty}
f(x)e^{i\xi x}dx
$$

Inverse transform:

$$
f(x)
=
\frac{1}{2\pi}
\int_{-\infty}^{\infty}
\widehat{f}(\xi)e^{-i\xi x}d\xi
$$

Derivative mapping:

$$
\frac{\partial}{\partial x}
\leftrightarrow
-i\xi
$$

---

# 4. Full-plane calibration limit

Before solving the layered system, the deep-interface limit

$$
h\to\infty
$$

is used to fix signs and phases.

The full-plane traction-displacement relation becomes

$$
\begin{bmatrix}
\widehat{\sigma}_{xy} \\
\widehat{\sigma}_{yy}
\end{bmatrix}
=
-\frac{2\mu|\xi|}{\kappa+1}
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
\begin{bmatrix}
\widehat{\Delta U} \\
\widehat{\Delta V}
\end{bmatrix}
$$

where

$$
\kappa=\frac{3-\nu}{1+\nu}
$$

for plane stress.

---

# 5. Crack-opening expansions

The crack-opening jumps are expanded using bounded basis functions.

## Normal opening

$$
\Delta V(x)
=
\frac{1}{\pi}
\sum_{n=1}^{N}
c_n
\cos\left[
(2n-1)\sin^{-1}(x/a)
\right]
$$

This basis is even in $begin:math:text$x$end:math:text$.

---

## Tangential opening

$$
\Delta U(x)
=
\frac{1}{\pi}
\sum_{n=1}^{N}
d_n
\sin\left[
2n\sin^{-1}(x/a)
\right]
$$

This basis is odd in $begin:math:text$x$end:math:text$.

---

# 6. Fourier transforms of the crack openings

Using the substitution

$$
x=a\sin\theta
$$

the Fourier transforms reduce to Bessel-function forms.

---

## Normal jump transform

$$
\widehat{\Delta V}(\xi)
=
\sum_{n=1}^{N}
c_n
\frac{2n-1}{\xi}
J_{2n-1}(a\xi)
$$

---

## Tangential jump transform

$$
\widehat{\Delta U}(\xi)
=
i
\sum_{n=1}^{N}
d_n
\frac{2n}{\xi}
J_{2n}(a\xi)
$$

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

with

$$
\mathbf{C}
=
\mathbf{C}^{(1)}
-
\mathbf{C}^{(2)}
$$

where:

- $begin:math:text$ \\mathbf\{C\}\^\{\(1\)\} $end:math:text$ is the finite-layer compliance
- $begin:math:text$ \\mathbf\{C\}\^\{\(2\)\} $end:math:text$ is the lower half-space compliance

The stiffness operator is

$$
\mathbf{K}
=
\mathbf{C}^{-1}
$$

---

# 8. Fourier-domain stiffness kernels

The transform-domain relation becomes

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
\mathbf{K}
=
\begin{bmatrix}
K_{11} & K_{12} \\
K_{21} & K_{22}
\end{bmatrix}
$$

Substituting the Bessel expansions produces the dual-integral equations.

---

# 9. Identification of q1, q2, q3, q4

Matching the inverse Fourier integrals gives:

$$
q_1(\xi)=K_{22}(\xi)
$$

$$
q_2(\xi)=iK_{21}(\xi)
$$

$$
q_3(\xi)=-iK_{12}(\xi)
$$

$$
q_4(\xi)=K_{11}(\xi)
$$

for the stress-component convention.

---

# 10. High-frequency asymptotics

The kernels satisfy:

$$
\frac{q_1}{\xi}\to -\frac14
$$

$$
\frac{q_4}{\xi}\to -\frac14
$$

while

$$
\frac{q_2}{\xi}\to 0
$$

$$
\frac{q_3}{\xi}\to 0
$$

These asymptotic parts are subtracted analytically before quadrature.

This significantly improves numerical stability.

---

# 11. Numerical method

The numerical solver uses:

- weighted least squares
- Schmidt/Galerkin projection
- QR stabilization
- asymptotic subtraction
- residual verification

The unknown coefficients are

$$
c_n,\ d_n
$$

The stress intensity factors are extracted from the high-frequency coefficient behavior.

---

# 12. Verification strategy

The implementation is verified using:

1. comparison against published Itou benchmark values
2. residual checks inside the crack
3. convergence with basis order $begin:math:text$N$end:math:text$
4. kernel asymptotics
5. condition-number monitoring

---

# 13. Thin-layer warning

For very small

$$
h/a
$$

the current basis becomes increasingly ill-conditioned.

Warning signs include:

- exploding condition number
- unstable $begin:math:text$K\_I\,K\_\{II\}$end:math:text$
- large residuals
- non-convergent basis sweep

In this regime, an asymptotic thin-layer basis is recommended.

---

# 14. Repository philosophy

This repository is intended as:

- a derivation audit trail
- a computational fracture-mechanics verification project
- an example of AI-assisted symbolic reconstruction

The implementation was reconstructed independently through:

1. operator derivation
2. asymptotic checks
3. kernel verification
4. numerical convergence
5. benchmark comparison
6. sign-convention auditing

rather than by directly copying the original paper derivation.
