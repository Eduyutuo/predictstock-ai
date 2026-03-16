/**
 * api.js - Capa de servicio para comunicación con el backend FastAPI.
 *
 * Centraliza todas las llamadas HTTP al API de PredictStock AI.
 */

import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Sube un archivo CSV/JSON con historial de ventas.
 * @param {File} file - Archivo CSV o JSON.
 * @returns {Promise} Respuesta con info de registros cargados.
 */
export async function uploadCSV(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/**
 * Obtiene predicción de demanda para un producto.
 * @param {string} productId - ID del producto.
 * @param {number} days - Horizonte de predicción (1-90).
 * @returns {Promise} Predicción con demanda, stock crítico y estado.
 */
export async function getPrediction(productId, days = 7) {
  const response = await api.get(`/predict/${productId}`, {
    params: { dias: days },
  });
  return response.data;
}

/**
 * Obtiene el inventario completo con alertas.
 * @returns {Promise} Lista de productos con estado de stock.
 */
export async function getInventory() {
  const response = await api.get('/inventory');
  return response.data;
}

/**
 * Obtiene analytics: KPIs, productos hueso, comparación ventas vs predicción.
 * @param {string|null} productId - Producto para gráfico comparativo.
 * @returns {Promise} Datos de analytics completos.
 */
export async function getAnalytics(productId = null) {
  const params = productId ? { producto_id: productId } : {};
  const response = await api.get('/analytics', { params });
  return response.data;
}

/**
 * Obtiene la lista de productos disponibles.
 * @returns {Promise} Lista de IDs de productos.
 */
export async function getProducts() {
  const response = await api.get('/products');
  return response.data;
}

/**
 * Verifica el estado del servicio.
 * @returns {Promise} Estado del servidor y modelo.
 */
export async function healthCheck() {
  const response = await api.get('/health');
  return response.data;
}

export default api;
