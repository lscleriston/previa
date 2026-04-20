import pytest


@pytest.mark.asyncio
async def test_dre_calculation_reflects_recovery_adjustments(api_client):
    response = await api_client.get("/api/resumo/cr?mes=2026-04")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    item_1 = next(item for item in data if item.get("cr") == "CR-001")
    item_3 = next(item for item in data if item.get("cr") == "CR-003")

    # CR-001 has a credit recovery adjustment of +500
    recovery_1 = next(previa for previa in item_1.get("previas", []) if previa.get("categoria") == "Recuperação Pessoal")
    assert recovery_1["valor"] == 500.0

    # CR-003 has a debit recovery adjustment of -250
    recovery_3 = next(previa for previa in item_3.get("previas", []) if previa.get("categoria") == "Recuperação Pessoal")
    assert recovery_3["valor"] == -250.0

    # Basic DRE formula from docs: MC = RL + (sum of recoveries and other cost adjustments)
    rl_1 = item_1.get("total_rl")
    rl_3 = item_3.get("total_rl")
    assert rl_1 == 10000.0
    assert rl_3 == 5000.0

    mc_1 = rl_1 + sum(previa["valor"] for previa in item_1.get("previas", []))
    mc_3 = rl_3 + sum(previa["valor"] for previa in item_3.get("previas", []))

    assert mc_1 == 10500.0
    assert mc_3 == 4750.0

    pct_1 = (mc_1 / rl_1) * 100 if rl_1 else None
    pct_3 = (mc_3 / rl_3) * 100 if rl_3 else None

    assert pct_1 == 105.0
    assert pct_3 == 95.0
