/**
 * Configurações do Frontend
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export const API_ENDPOINTS = {
  // V1 Endpoints (novo contrato)
  analysis: `${API_BASE_URL}/api/v1/analysis`,
  analyze: `${API_BASE_URL}/api/v1/analyze`,
  
  // Legacy endpoints
  mockAnalysis: `${API_BASE_URL}/mock/analysis`,
  chat: `${API_BASE_URL}/chat`,
  culturas: `${API_BASE_URL}/culturas`,
  health: `${API_BASE_URL}/health`,
}

export const API_CONFIG = {
  timeout: 30000, // 30 segundos
  retries: 1,
}
