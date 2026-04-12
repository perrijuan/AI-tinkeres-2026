# SafraViva Backend

Este diretório contém o backend do MVP do SafraViva.

Pontos principais:
- Recebe polígono e contexto agronômico.
- Deriva contexto espacial (centroide, bbox, área e município).
- Calcula forecast simplificado para 14 dias (modo MVP).
- Enriquecimento com contexto agrícola + ZARC heurístico.
- Calcula score de risco explicável.
- Retorna payload final pronto para o frontend.

Entrada/saída oficial em `docs/api_contract.md`.
