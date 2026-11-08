#!/usr/bin/env python3
"""RZOTKIEWKA AI v2.2 (LAB): bezpieczna kalibracja 1X2 dla bazowego v2.0.

Kalibracja bez informacji o przyszlych wynikach. Model nie jest uruchamiany
w produkcji; korzysta z zapisanego w raporcie 2.1 `old_p_*` (bazowy 2.0).
Optymalizacja Brier + regularyzacja L2, standard library only.
"""
from __future__ import annotations

import math

OUTCOMES = ('1', 'X', '2')
PENALTY = 0.05   # stala regularyzacji, nie dobierana do sezonu testowego
MIN_PROB = 1e-10
MAX_ITER = 250


def calibrated_probs(base, params):
    """3-klasowe prawdopodobienstwa: p_i^(exp(t)) * exp(b_i)."""
    if set(base) != set(OUTCOMES):
        raise ValueError('Potrzebne prawdopodobienstwa 1, X, 2')
    p = [float(base[k]) for k in OUTCOMES]
    if any(not math.isfinite(x) or x < 0 or x > 1 for x in p) or abs(sum(p) - 1) > 0.00001:
        raise ValueError('Nieprawidlowe prawdopodobienstwa bazowe')
    if len(params) != 3 or any(not math.isfinite(x) or abs(x) > 4 for x in params):
        raise ValueError('Nieprawidlowe parametry kalibracji')
    temperature, draw_bias, away_bias = params
    power = math.exp(temperature)
    z = [power * math.log(max(MIN_PROB, x)) + b for x, b in zip(p, (0., draw_bias, away_bias))]
    zmax = max(z)
    exps = [math.exp(x - zmax) for x in z]
    denom = sum(exps)
    return dict(zip(OUTCOMES, (x / denom for x in exps)))


def score(probs, outcome):
    return {
        'brier': sum((probs[k] - (k == outcome)) ** 2 for k in OUTCOMES),
        'log_loss': -math.log(max(MIN_PROB, probs[outcome])),
        'pick': max(OUTCOMES, key=lambda k: probs[k]),
    }


def loss_and_gradient(rows, params, penalty=PENALTY):
    """Wiersze: (slownik prawdopodobienstw, wynik 1/X/2)."""
    if not rows:
        raise ValueError('Brak danych treningowych')
    t, bx, b2 = params
    power = math.exp(t)
    obj = grad_t = grad_x = grad_2 = 0.0
    for base, outcome in rows:
        p = [base[k] for k in OUTCOMES]
        logs = [math.log(max(MIN_PROB, v)) for v in p]
        z = [power * logs[0], power * logs[1] + bx, power * logs[2] + b2]
        zmax = max(z)
        a = [math.exp(v-zmax) for v in z]
        s = sum(a)
        a = [v/s for v in a]
        errors = [a[i] - int(OUTCOMES[i] == outcome) for i in range(3)]
        obj += sum(e*e for e in errors)
        common = sum(errors[i] * a[i] for i in range(3))
        ds = [2 * a[i] * (errors[i] - common) for i in range(3)]
        grad_t += sum(ds[i] * power * logs[i] for i in range(3))
        grad_x += ds[1]
        grad_2 += ds[2]
    n = len(rows)
    reg = penalty * sum(x*x for x in params)
    gradient = [grad_t/n+2*penalty*t, grad_x/n+2*penalty*bx,
                grad_2/n+2*penalty*b2]
    return obj/n + reg, gradient


def fit(rows, penalty=PENALTY):
    """Deterministyczny gradient descent z backtracking. NIE uzywaj testu."""
    rows = list(rows)
    params = [0.0, 0.0, 0.0]
    current, grad = loss_and_gradient(rows, params, penalty)
    for _ in range(MAX_ITER):
        norm = sum(x*x for x in grad)
        if norm < 1e-14:
            break
        step = 1.0
        accepted = False
        for _ in range(24):
            trial = [x-step*g for x, g in zip(params, grad)]
            trial_loss, trial_grad = loss_and_gradient(rows, trial, penalty)
            if trial_loss < current - 1e-6 * step * norm:
                params, current, grad = trial, trial_loss, trial_grad
                accepted = True
                break
            step *= 0.5
        if not accepted:
            break
    return tuple(round(x, 10) for x in params)
