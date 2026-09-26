"""Cumulative textbook experiments. Synthetic parameters; all quantities SI.

Run from the repository root: python projects/depth_lab.py
No network, no hardware effects. Writes JSON and SVG beneath projects/results.
"""
from pathlib import Path
import json
import numpy as np
from scipy.constants import epsilon_0, elementary_charge, Boltzmann, electron_mass, hbar
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import betaln
from scipy.stats import norm, binom
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

Q = elementary_charge
EPS = 11.7 * epsilon_0
VT = Boltzmann * 300 / Q
NA = 1e23
NI = 1e16
CI = 3.9 * epsilon_0 / 3e-9
OUT = Path(__file__).resolve().parent / "results"


def mos_charge(psi, na=NA, ni=NI, vt=VT, eps=EPS):
    """Equilibrium p-type half-space charge, C/m^2; psi in volts.

    Fully ionized net acceptors represented by p0 - n0; Boltzmann carriers.
    na names bulk hole density p0, approximately net acceptor density.
    Range bounded to prevent exponential overflow and invalid extrapolation.
    """
    if min(na, ni, vt, eps) <= 0 or not np.isfinite(psi):
        raise ValueError("finite potential and positive physical inputs required")
    u = psi / vt
    if abs(u) > 60:
        raise ValueError("outside this numerical teaching model's range")
    r = (ni / na) ** 2
    f = np.expm1(-u) + u + r * (np.expm1(u) - u)
    return -np.sign(u) * np.sqrt(2 * eps * Q * na * vt * max(f, 0))


def gate_voltage(psi, ci=CI, vfb=0):
    if ci <= 0:
        raise ValueError("positive capacitance required")
    return vfb + psi - mos_charge(psi) / ci


def surface_potential(vg, ci=CI, vfb=0):
    """Unique equilibrium root in a stated bounded search interval."""
    if not np.isfinite(vg):
        raise ValueError("finite gate bias required")
    return brentq(lambda p: gate_voltage(p, ci, vfb) - vg, -0.3, 1.3,
                  xtol=1e-13)


def electrostatics():
    phi = VT * np.log(NA / NI)
    threshold = gate_voltage(2 * phi)
    psis = np.linspace(-0.2, 1.1, 501)
    charges = np.array([mos_charge(p) for p in psis])
    depletion = -np.sqrt(2 * EPS * Q * NA * np.maximum(psis, 0))
    errors = []
    # Independently integrate rho(psi) and compare the Poisson first integral.
    for psi in [-0.15, 0.05, 0.3, 0.7, 1.0]:
        rho = lambda v: Q * NA * (
            np.exp(-v / VT) - 1 - (NI / NA) ** 2 * np.expm1(v / VT))
        integral = quad(rho, 0, psi, epsabs=1e-12)[0]
        q_quad = -np.sign(psi) * np.sqrt(-2 * EPS * integral)
        errors.append(abs(q_quad - mos_charge(psi)))
    gates = np.linspace(-1, 3, 101)
    roots = np.array([surface_potential(v) for v in gates])
    residual = max(abs(gate_voltage(p) - v) for p, v in zip(roots, gates))
    assert max(errors) < 1e-12
    assert residual < 1e-10
    assert np.all(np.diff(roots) > 0)
    assert mos_charge(0) == 0
    # A physical limiting case: approaching flat band gives Debye capacitance.
    delta = 1e-7
    capacitance = -(mos_charge(delta) - mos_charge(-delta)) / (2 * delta)
    debye = np.sqrt(EPS * Q * NA / VT * (1 + (NI / NA) ** 2))
    assert abs(capacitance / debye - 1) < 1e-5
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(psis, charges * 100, label="Equilibrium Poisson–Boltzmann")
    ax[0].plot(psis, depletion * 100, "--", label="Depletion approximation")
    ax[0].set(xlabel="Surface potential (V)", ylabel="Charge (µC/cm²)",
              ylim=(-2, 1))
    ax[0].legend(fontsize=8)
    ax[1].plot(gates, roots)
    ax[1].axhline(2 * phi, ls="--", color="gray", label="2φF convention")
    ax[1].set(xlabel="Gate voltage (V)", ylabel="Surface potential (V)")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "deep-electrostatics.svg")
    plt.close(fig)
    return {"bulk_hole_density_m-3": NA, "intrinsic_density_m-3": NI,
            "oxide_F_m-2": CI, "phi_F_V": phi, "threshold_V": threshold,
            "charge_quadrature_max_error_C_m-2": max(errors),
            "gate_residual_max_V": residual,
            "flat_band_capacitance_F_m-2": capacitance,
            "root_at_gate_1V": surface_potential(1),
            "trap_shift_for_1e11_cm-2_V": -Q * 1e15 / CI}


def materials():
    """Normalized wall energy and series-stiffness bifurcation."""
    density = lambda z: 0.5 / np.cosh(z / np.sqrt(2)) ** 4
    wall = quad(density, -30, 30)[0]
    exact = 2 * np.sqrt(2) / 3
    assert abs(wall - exact) < 1e-10
    etas = np.array([0, .25, .5, .75, .99, 1.01])
    states = np.sqrt(np.maximum(1 - etas, 0))
    barrier = np.maximum(1 - etas, 0) ** 2 / 4
    return {"normalized_wall_energy": wall, "analytic_wall_energy": exact,
            "series_stiffness": etas.tolist(), "stable_magnitude": states.tolist(),
            "barrier": barrier.tolist()}


def inverse_design():
    """Scaled linear sensitivity: clustered versus spread experimental inputs."""
    rows = []
    for label, x in [("clustered", np.linspace(.99, 1.01, 101)),
                     ("spread", np.linspace(-1, 1, 101))]:
        matrix = np.column_stack([x, np.ones_like(x)])
        singular = np.linalg.svd(matrix, compute_uv=False)
        covariance = .01 ** 2 * np.linalg.inv(matrix.T @ matrix)
        rows.append({"design": label, "condition_number": float(singular[0] / singular[-1]),
                     "slope_standard_error": float(np.sqrt(covariance[0, 0]))})
    assert rows[0]["slope_standard_error"] > 90 * rows[1]["slope_standard_error"]
    return rows


def programming():
    tau0, ea, target = 1e-9, 2e8, 1e-6
    rows = []
    for width in [20e-9, 50e-9, 100e-9, 200e-9]:
        field = ea / np.log(width / (tau0 * np.log(1 / target)))
        failure = np.exp(-width / (tau0 * np.exp(ea / field)))
        assert abs(failure / target - 1) < 1e-12
        rows.append({"pulse_ns": width * 1e9, "field_MV_cm": field / 1e8})
    # Jensen counterexample: mean switching rate does not predict survival.
    width = 100e-9
    rates = np.array([1 / 2e-9, 1 / 20e-9])
    mixture = np.mean(np.exp(-width * rates))
    mean_rate_prediction = np.exp(-width * np.mean(rates))
    assert mixture > mean_rate_prediction
    return {"field_frontier": rows, "two_population_failure": mixture,
            "mean_rate_prediction": mean_rate_prediction}


def array_and_ecc():
    n, mean, corr = 72, 1e-5, .001
    total = 1 / corr - 1
    alpha, beta = mean * total, (1 - mean) * total
    log_p0 = betaln(alpha, beta + n) - betaln(alpha, beta)
    log_p1 = np.log(n) + betaln(alpha + 1, beta + n - 1) - betaln(alpha, beta)
    correlated = -np.expm1(log_p0) - np.exp(log_p1)
    independent = binom.sf(1, n, mean)
    assert correlated > independent
    rows = []
    for count in [32, 64, 128, 256]:
        delay = sum(range(1, count + 1))
        assert delay == count * (count + 1) / 2
        rows.append({"segments": count, "delay_in_rc_units": delay})
    required = 2 * .0532 * norm.isf(.001)
    uncertainty = .4 / (2 * norm.isf(.001)) - .0532
    return {"elmore": rows, "SEC_word_error_independent": independent,
            "SEC_word_error_beta_binomial": correlated,
            "bit_correlation": corr, "required_window_V": required,
            "extra_sigma_budget_V": uncertainty}


def controller_enumeration():
    """Finite reference transition enumeration, not an HDL equivalence proof."""
    checked = 0
    for busy, remaining in [(False, 0)] + [(True, n) for n in range(1, 256)]:
        for reset in [False, True]:
            for valid in [False, True]:
                ready = not busy and not reset
                accepted = valid and ready
                commit = busy and remaining == 1 and not reset
                assert not (accepted and commit)
                assert not reset or not (accepted or commit)
                checked += 1
    # No further reset/fault: a request accepted at edge zero commits at edge L.
    traces = []
    for latency in [1, 2, 4, 255]:
        remaining = latency
        for edge in range(1, latency + 1):
            commit = remaining == 1
            assert commit == (edge == latency)
            remaining -= 1
        traces.append({"latency_cycles": latency, "completion_edge": edge,
                       "earliest_next_acceptance_edge": edge + 1})
    return {"reference_admission_cases": checked, "traces": traces,
            "limit": "Not a replacement for the delivered RTL and gate simulations"}


def integration():
    # Junctions coupled to each other and to ambient by thermal conductance.
    conductance = np.array([[3., -1.], [-1., 2.]])
    power = np.array([20., 5.])
    rise = np.linalg.solve(conductance, power)
    assert np.max(abs(conductance @ rise - power)) < 1e-12
    defect_load = 1.
    poisson = np.exp(-defect_load)
    clustered = (1 + defect_load / 2) ** -2
    return {"two_node_power_W": power.tolist(), "temperature_rise_K": rise.tolist(),
            "poisson_yield_at_DA1": poisson, "clustered_yield_alpha2_at_DA1": clustered,
            "wafer_independent_two_tier_yield": poisson ** 2,
            "known_good_die_bond_yield_example": .98}


def workload_and_queue():
    rows = []
    for batch in [1, 2, 4, 8, 16]:
        context = 128
        kv = 2 * 16 * 4 * 64 * 2 * batch * context
        ops = 2 * 16e6 * batch + 4 * 16 * 4 * 64 * batch * context
        traffic = 16e6 + kv
        compute, memory = ops / 1e12, traffic / 80e9
        service = max(compute, memory) + 20e-6
        rows.append({"batch": batch, "context": context, "KV_bytes": kv,
                     "FLOPs_per_byte": ops / traffic, "service_s": service,
                     "tokens_per_s": batch / service,
                     "bottleneck": "compute" if compute > memory else "memory"})
    service = rows[-1]["service_s"]
    deadline = .005
    mean_limit = 1 - service / deadline
    tail_limit = 1 - service * np.log(100) / deadline
    assert tail_limit < mean_limit
    return {"fixed_context_batch_sweep": rows,
            "M_M_1_mean_5ms_utilization_limit": mean_limit,
            "M_M_1_p99_5ms_utilization_limit": tail_limit,
            "M_D_1_mean_at_rho_0_7_s": service * (1 + .7 / (2 * (1 - .7))),
            "M_M_1_mean_at_rho_0_7_s": service / (1 - .7)}


def uncertainty():
    # Joint worst-case read-margin constraint, not independent optimistic values.
    target = .001
    sigma_high, coupling_low = .0532 * 1.2, (.4 / .13) * .8
    required = 2 * norm.isf(target) * sigma_high / coupling_low
    nominal = 2 * norm.isf(target) * .0532 / (.4 / .13)
    assert abs(required / nominal - 1.5) < 1e-12
    # Illustrative binary-measurement design information at p=1/2 is strongest.
    return {"nominal_required_Pr_C_m2": nominal,
            "box_robust_required_Pr_C_m2": required,
            "increase_factor": required / nominal,
            "evidence": "Assumed independent uncertainty box, not measured confidence bounds"}


def worked_examples():
    """Check scalar examples and boundaries introduced by the expanded prose."""
    kappa = np.sqrt(2 * .2 * electron_mass * Q) / hbar
    max_context = int((64 * 2**20 - 16_000_000 - 8 * 2**20) / 262144)
    assert max_context == 162
    assert 16_000_000 + 8 * 2**20 + max_context * 262144 <= 64 * 2**20
    assert 16_000_000 + 8 * 2**20 + (max_context + 1) * 262144 > 64 * 2**20
    ops, traffic = 545554432, 49554432
    new_step = max(ops / 1e12, traffic / 160e9) + 20e-6
    # Limit cases and invalid numerical domains must be explicit.
    rejected = 0
    for call in [lambda: mos_charge(0.2, na=-1), lambda: mos_charge(float('nan')),
                 lambda: mos_charge(100), lambda: gate_voltage(.1, ci=0)]:
        try:
            call()
        except ValueError:
            rejected += 1
    assert rejected == 4
    field_fraction = (10 / 33) / (10 / 33 + 1 / 3.9)
    return {"tunnel_kappa_nm-1": kappa * 1e-9,
            "transmission_ratio_for_0_1nm_increase": np.exp(-2 * kappa * .1e-9),
            "linear_FE_voltage_fraction": field_fraction,
            "sampled_thermal_noise_100fF_300K_V": np.sqrt(Boltzmann * 300 / 100e-15),
            "required_integration_time_ns": 2 * norm.isf(.001) * .005 * 100e-15 / 10e-6 * 1e9,
            "independent_extra_noise_sigma_V": np.sqrt((.4 / (2 * norm.isf(.001)))**2 - .0532**2),
            "maximum_context_at_batch16": max_context,
            "doubled_interface_step_s": new_step,
            "doubled_interface_tokens_s": 16 / new_step,
            "M_M_1_p99_at_rho_0_7_s": np.log(100) * .0006394304 / .3,
            "retention_log_sensitivity_per_K": -.7 / (Boltzmann / Q * 300**2),
            "zero_failure_trials_for_1e-9_95pct": np.ceil(np.log(.05) / np.log1p(-1e-9)),
            "invalid_domain_cases_rejected": rejected}


def main():
    OUT.mkdir(exist_ok=True)
    result = {"evidence": "Original synthetic teaching experiments",
              "electrostatics": electrostatics(), "materials": materials(),
              "inverse_design": inverse_design(), "programming": programming(),
              "array_and_ecc": array_and_ecc(), "controller": controller_enumeration(),
              "integration": integration(), "workload_and_queue": workload_and_queue(),
              "uncertainty": uncertainty(), "worked_examples": worked_examples()}
    (OUT / "depth-lab.json").write_text(json.dumps(result, indent=2),
                                       encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
