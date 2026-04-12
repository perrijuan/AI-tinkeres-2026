# Frontend Adaptações - Novo Contrato API

## 🎯 Alterações Realizadas

Frontend foi atualizado para trabalhar com o novo contrato da API (`/api/v1/analysis`).

### 1. **DemoPage.tsx**
- ✅ Campo novo: **Data de Plantio** (sowing_date)  
  - Adicionado no Step 1 com date picker
  - Padrão: hoje
  
- ✅ Novo Payload (`/api/v1/analysis`)
  ```json
  {
    "field_id": "identificador_gerado",
    "property_name": "Empresa ou Nome",
    "culture": "soja",
    "sowing_date": "2026-04-12",
    "crop_stage": null,
    "irrigated": false,
    "analysis_timestamp": "2026-04-12T20:30:00Z",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[lon, lat], [lon, lat], ...]]
    }
  }
  ```

### 2. **ResultsPage.tsx**
- ✅ Compatibilidade com nova resposta
  - Fallbacks para campos opcionais (wind_mean_7d_ms, crop_stage)
  - Valores padrão para data_sources (se não enviado pelo backend)
  - Gráfico NDVI renderizado condicionalmente

### 3. **Configuration**
- ✅ Arquivo `src/config.ts` criado
  - Centraliza URLs da API
  - Suporta VITE_API_BASE_URL env var
  - Endpoints predefinidos

### 4. **Environment**
- ✅ `.env.example` criado
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```

## 🚀 Como Usar

### Ambiente Local
```bash
# No frontend/
npm install
npm run dev
```

### Produção
```bash
# Criar .env com o endpoint correto
VITE_API_BASE_URL=https://seu-backend.com

# Build
npm run build
```

## 📋 Compatibilidade

| Endpoint | Status | Notas |
|----------|--------|-------|
| `/api/v1/analysis` | ✅ Novo | Contrato novo, recomendado |
| `/api/v1/analyze` | ✅ Alias | Mesmo que acima |
| `/mock/analysis` | ✅ Legacy | Fallback para ResultsPage se não tiver dados |
| `/chat` | ✅ Funcional | Dependente de conversation_id |
| `/culturas` | ✅ Mantém | Listagem de culturas |
| `/health` | ✅ Mantém | Health check |

## 📝 Request/Response

### Request para `/api/v1/analysis`
```json
{
  "field_id": "talhao_01_1712973600000",
  "property_name": "Minha Fazenda",
  "culture": "soja",
  "sowing_date": "2026-04-12",
  "crop_stage": null,
  "irrigated": false,
  "analysis_timestamp": "2026-04-12T20:30:00.000Z",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-55.8126, -12.4321],
      [-55.7421, -12.4321],
      [-55.7421, -12.4888],
      [-55.8126, -12.4888],
      [-55.8126, -12.4321]
    ]]
  }
}
```

### Response esperado
```json
{
  "field_info": {...},
  "summary": {...},
  "metrics": {...},
  "risk_flags": {...},
  "forecast_timeseries": [...],
  "map_layer": {...},
  "copilot_response": {...},
  "data_sources": {...} // Opcional
}
```

## ⚙️ Variáveis de Ambiente

```env
# Mínimo necessário
VITE_API_BASE_URL=http://localhost:8000

# Desenvolvimento
VITE_API_BASE_URL=http://localhost:8000

# Produção
VITE_API_BASE_URL=https://api-production.safraviva.com.br
```

## 🔄 Fallbacks Implementados

1. **data_sources**: Se não vir na resposta, usa valores padrão
2. **wind_mean_7d_ms**: Métrica renderizada condicionalmente
3. **crop_stage**: Campo renderizado só se tiver valor
4. **conversation_id**: Chat renderizado só se existir

## ✅ Testes Recomendados

1. [ ] Fluxo completo: Step 1 → Step 2 → Step 3 → Análise
2. [ ] Verificar payload enviado (DevTools Network)
3. [ ] Renderização da resposta completa
4. [ ] Sem conversation_id (chat não deve renderizar)
5. [ ] Com conversation_id (chat deve renderizar)

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| "Backend online?" | Verificar `VITE_API_BASE_URL` em `.env` |
| Payload com lat/lon trocado | Geometry usa `[lon, lat]` GMagain |
| Wind_mean não aparece | Campo opcional, back pode não enviar |
| Chat não renderiza | Verificar se response inclui `conversation_id` |

## 📚 Referências

- [API Contract - backend/docs/api_contract.md](../backend/docs/api_contract.md)
- [Example Request - backend/docs/example_request.json](../backend/docs/example_request.json)
- [Example Response - backend/docs/example_response.json](../backend/docs/example_response.json)
