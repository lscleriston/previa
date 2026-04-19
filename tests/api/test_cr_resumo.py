import pytest


@pytest.mark.asyncio
async def test_resumo_por_cr_returns_expected_data(api_client):
    response = await api_client.get("/api/resumo/cr?mes=2026-04")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert any(item.get("cr") == "CR-001" for item in data)
    assert any(item.get("cr") == "CR-002" for item in data)

    recovery_item = next(item for item in data if item.get("cr") == "CR-001")
    assert any(previa.get("categoria") == "Recuperação Pessoal" for previa in recovery_item.get("previas", []))

    recovery_item_3 = next(item for item in data if item.get("cr") == "CR-003")
    recovery_previas_3 = [previa for previa in recovery_item_3.get("previas", []) if previa.get("categoria") == "Recuperação Pessoal"]
    assert len(recovery_previas_3) == 1
    assert recovery_previas_3[0]["valor"] == -250.0
