# modules/mathfin.py
# Funções matemáticas financeiras.
# Equivalente a functionsgeral.h do programa C.

def ratepera_to_rateperm(rpa):
    """Converte taxa anual (%) para taxa mensal (%)."""
    return ((1.0 + rpa / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0


def rateperm_to_ratepera(rpm):
    """Converte taxa mensal (%) para taxa anual (%)."""
    return ((1.0 + rpm / 100.0) ** 12.0 - 1.0) * 100.0


def rateperm_to_rateperxm(rpm, m):
    """Converte taxa mensal (%) para taxa por X meses (%)."""
    return ((1.0 + rpm / 100.0) ** m - 1.0) * 100.0


def rateperxm_to_rateperm(rpxm, m):
    """Converte taxa por X meses (%) para taxa mensal (%)."""
    return ((1.0 + rpxm / 100.0) ** (1.0 / m) - 1.0) * 100.0


def calculates_total_and_final_amount(amount, contribution, rate_pm, period_months):
    """
    Calcula montante total aportado e montante final com juros compostos.

    :param amount:          Quantia inicial
    :param contribution:    Aporte mensal
    :param rate_pm:         Taxa de juros mensal (%)
    :param period_months:   Período em meses (int)
    :return:                (total_amount, final_amount)
    """
    total_amount = period_months * contribution + amount
    final_amount = amount * (1.0 + rate_pm / 100.0) ** period_months

    var = 0.0
    for _ in range(period_months):
        var = (contribution + var) * (1.0 + rate_pm / 100.0)

    final_amount += var
    return total_amount, final_amount
