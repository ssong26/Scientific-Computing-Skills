"""
parallel_crack_sif_fast.py

Fast single-run wrapper for the subsurface parallel-crack SIF solver.

Usage:
    python parallel_crack_sif_fast.py --h_over_a 0.1
    python parallel_crack_sif_fast.py --h_over_a 0.05 --nu 0.3

Output:
    KI_norm  = KI  / (p*sqrt(pi*a))
    KII_norm = KII / (p*sqrt(pi*a))

This script imports the core solver from parallel_crack_sif_verified.py.  Keep the
two files in the same folder.
"""
from __future__ import annotations

import argparse
from parallel_crack_sif_verified import solve_sif, print_one


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast SIF calculation for a crack parallel to a free surface.")
    parser.add_argument("--h_over_a", type=float, required=True, help="Depth ratio h/a")
    parser.add_argument("--nu", type=float, default=0.3, help="Poisson ratio; weak effect for this benchmark")
    parser.add_argument("--p", type=float, default=1.0)
    parser.add_argument("--a", type=float, default=1.0)
    parser.add_argument("--n_terms", type=int, default=14)
    parser.add_argument("--n_quad", type=int, default=60)
    parser.add_argument("--weight_power", type=float, default=0.5)
    parser.add_argument("--xi_max_factor", type=float, default=160.0)
    parser.add_argument("--epsabs", type=float, default=1e-7)
    parser.add_argument("--epsrel", type=float, default=1e-6)
    parser.add_argument("--no_check", action="store_true", help="Skip off-grid residual diagnostics")
    args = parser.parse_args()

    res = solve_sif(
        h_over_a=args.h_over_a,
        nu=args.nu,
        p=args.p,
        a=args.a,
        n_terms=args.n_terms,
        n_quad=args.n_quad,
        weight_power=args.weight_power,
        xi_max_factor=args.xi_max_factor,
        epsabs=args.epsabs,
        epsrel=args.epsrel,
        check=not args.no_check,
    )
    print_one(res)
    if args.h_over_a < 0.05:
        print("\nWarning: h/a is small. Use parallel_crack_sif_verified.py for N-convergence and residual checks.")


if __name__ == "__main__":
    main()
