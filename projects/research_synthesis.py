"""Reproduce illustrative synthesis examples; no measured-device prediction."""
import json
import math
from pathlib import Path
from statistics import NormalDist


def symbol_error(window, sigma, levels):
    """Equal-prior Gaussian levels with midpoint decisions; return symbol error."""
    if (not math.isfinite(window) or window < 0
            or not math.isfinite(sigma) or sigma <= 0
            or isinstance(levels, bool) or not isinstance(levels, int)
            or levels < 2):
        raise ValueError("Use a finite nonnegative span, positive width, and L>=2")
    margin = window / (2 * sigma * (levels - 1))
    tail = 0.5 * math.erfc(margin / math.sqrt(2))
    return 2 * (levels - 1) / levels * tail


def first_cheaper_query(preparation, direct, surrogate):
    """First positive integer N with preparation + N*surrogate < N*direct."""
    if (not all(math.isfinite(x) for x in (preparation, direct, surrogate))
            or preparation < 0 or surrogate < 0 or direct <= surrogate):
        raise ValueError("Nonnegative costs and direct > surrogate required")
    return math.floor(preparation / (direct - surrogate)) + 1


def main():
    crossover = 100 * math.log(2)
    window_a = lambda t: 0.6 + 0.6 * math.exp(-t / 100)
    assert math.isclose(window_a(crossover), 0.9)
    assert window_a(0) > 0.9 > window_a(1000)
    errors = {str(n): symbol_error(1.2, 0.05, n) for n in (2, 4, 8, 16)}
    # Independent limits: a collapsed span yields chance-level classification;
    # binary thresholding yields a single Gaussian tail, without the L factor.
    assert math.isclose(symbol_error(0, 1, 8), 7 / 8)
    assert math.isclose(symbol_error(2, 1, 2), 1 - NormalDist().cdf(1))
    assert errors['4'] < errors['8'] < errors['16']
    z = NormalDist().inv_cdf(1 - 0.001 / 2)
    spans = {str(n): (n - 1) * 2 * z * 0.05 for n in (8, 16)}
    for n, span in spans.items():
        # The worst interior-state requirement is sufficient for average error.
        assert symbol_error(span, 0.05, int(n)) <= 0.001
    first = first_cheaper_query(100, 1, 0.001)
    assert first == 101
    assert 100 + (first - 1) * 0.001 >= first - 1
    assert 100 + first * 0.001 < first
    rejected = 0
    for args in [(-1, .05, 4), (1, 0, 4), (1, .05, 1),
                 (float('nan'), .05, 4), (1, .05, 4.5)]:
        try:
            symbol_error(*args)
        except ValueError:
            rejected += 1
    assert rejected == 5
    try:
        first_cheaper_query(100, 1, 2)
    except ValueError:
        rejected += 1
    assert rejected == 6
    result = {
        'evidence': 'Original illustrative calculations, not measured parameters',
        'retention_crossover_s': crossover,
        'window_A_at_1ms_V': window_a(.001),
        'window_A_at_1000s_V': window_a(1000),
        'equal_prior_symbol_error_at_1_2V_span_0_05V_sigma': errors,
        'span_for_interior_error_at_most_0_001_V': spans,
        'electrical_then_anneal_normalized_defects': .2 * (0 + 1),
        'anneal_then_electrical_normalized_defects': .2 * 0 + 1,
        'first_cheaper_surrogate_query': first,
        'surrogate_plus_TCAD_error_bound_mV': 5 + 40,
        'total_energy_ratio_for_2pct_share_halved': 1 - .02 * .5,
        'invalid_inputs_rejected': rejected,
    }
    out = Path(__file__).resolve().parent / 'results' / 'research-synthesis.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
