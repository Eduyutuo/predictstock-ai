/**
 * Dashboard.jsx - Componente principal del dashboard de PredictStock AI.
 *
 * Muestra KPIs, gráfico comparativo ventas reales vs predicción de IA,
 * y tabla de inventario con alertas visuales.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Area, AreaChart, BarChart, Bar,
} from 'recharts';
import {
  TrendingUp, Package, AlertTriangle, BarChart3,
  ShoppingCart, DollarSign, Upload, RefreshCw, Activity,
  ArrowUpRight, ArrowDownRight, Boxes, Skull,
} from 'lucide-react';
import { getAnalytics, getInventory, getProducts, uploadCSV } from '../services/api';

/* ──────────────────────────────────────────────
   Custom Tooltip for Charts
   ────────────────────────────────────────────── */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card" style={{ padding: '12px 16px', minWidth: 180 }}>
      <p className="text-xs font-semibold mb-2" style={{ color: '#94a3b8' }}>{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-sm py-0.5">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span style={{ color: '#94a3b8' }}>{entry.name}:</span>
          <span className="font-semibold" style={{ color: '#f1f5f9' }}>
            {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ──────────────────────────────────────────────
   KPI Card Component
   ────────────────────────────────────────────── */
function KPICard({ title, value, subtitle, icon: Icon, glowClass, trend, delay }) {
  return (
    <div className={`glass-card p-5 sm:p-6 ${glowClass} animate-fade-in-up stagger-${delay}`}>
      <div className="flex items-start justify-between mb-4">
        <div
          className="p-3 rounded-xl"
          style={{ background: 'rgba(255,255,255,0.05)' }}
        >
          <Icon size={22} style={{ color: '#94a3b8' }} />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            trend >= 0
              ? 'text-emerald-400 bg-emerald-400/10'
              : 'text-rose-400 bg-rose-400/10'
          }`}>
            {trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <h3
        className="text-2xl font-bold mb-1 tracking-tight"
        style={{ color: '#f1f5f9' }}
      >
        {value}
      </h3>
      <p className="text-xs font-medium" style={{ color: '#94a3b8' }}>
        {title}
      </p>
      {subtitle && (
        <p className="text-xs mt-1" style={{ color: '#64748b' }}>{subtitle}</p>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────
   Alert Badge Component
   ────────────────────────────────────────────── */
function AlertBadge({ type }) {
  const classes = {
    ROJO: 'badge-red',
    AMARILLO: 'badge-yellow',
    VERDE: 'badge-green',
  };
  const labels = {
    ROJO: 'Stock Bajo',
    AMARILLO: 'Baja Rotación',
    VERDE: 'Saludable',
  };
  return <span className={classes[type] || 'badge-green'}>{labels[type] || type}</span>;
}

/* ──────────────────────────────────────────────
   Main Dashboard Component
   ────────────────────────────────────────────── */
export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [inventory, setInventory] = useState(null);
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  /** Carga los datos principales del dashboard */
  const loadData = useCallback(async (productId = null) => {
    try {
      setLoading(true);
      setError(null);
      const [analyticsData, inventoryData, productsData] = await Promise.all([
        getAnalytics(productId).catch(() => null),
        getInventory().catch(() => null),
        getProducts().catch(() => ({ products: [], trained: [] })),
      ]);

      if (analyticsData) setAnalytics(analyticsData);
      if (inventoryData) setInventory(inventoryData);
      setProducts(productsData.products || []);

      if (!productId && productsData.trained?.length > 0) {
        setSelectedProduct(productsData.trained[0]);
      }
    } catch (err) {
      setError('No se pudieron cargar los datos. Asegúrese de que el servidor está activo.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  /** Carga inicial */
  useEffect(() => {
    loadData();
  }, [loadData]);

  /** Actualiza gráfico cuando cambia el producto seleccionado */
  useEffect(() => {
    if (selectedProduct) {
      getAnalytics(selectedProduct)
        .then((data) => setAnalytics((prev) => ({ ...prev, ...data })))
        .catch(console.error);
    }
  }, [selectedProduct]);

  /** Maneja la subida de archivos CSV */
  const handleUpload = async (file) => {
    if (!file) return;
    try {
      setUploading(true);
      setUploadMessage(null);
      const result = await uploadCSV(file);
      setUploadMessage({
        type: 'success',
        text: `${result.mensaje} — ${result.registros_cargados} registros, ${result.productos_unicos} productos.`,
      });
      await loadData();
    } catch (err) {
      setUploadMessage({
        type: 'error',
        text: `Error: ${err.response?.data?.detail || err.message}`,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) handleUpload(file);
  };

  // ── Format helpers ──
  const fmt = (n, dec = 0) => {
    if (typeof n !== 'number' || isNaN(n)) return '—';
    return n.toLocaleString('es-MX', { maximumFractionDigits: dec });
  };

  const fmtCurrency = (n) => {
    if (typeof n !== 'number' || isNaN(n)) return '—';
    return `$${n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Simplified chart data — last 30 points to keep it readable
  const chartData = analytics?.comparacion_ventas_prediccion?.slice(-30) || [];

  /* ───────── RENDER ───────── */
  return (
    <div className="min-h-screen" style={{ background: '#0a0e1a' }}>
      {/* ── Header ── */}
      <header
        className="sticky top-0 z-50"
        style={{
          background: 'rgba(10, 14, 26, 0.85)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
        }}
      >
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 sm:gap-0">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-xl"
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              }}
            >
              <Activity size={22} color="white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight" style={{ color: '#f1f5f9' }}>
                PredictStock AI
              </h1>
              <p className="text-xs" style={{ color: '#64748b' }}>
                Gestión Predictiva de Inventarios
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {analytics && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow" />
                <span className="text-xs font-medium text-emerald-400">Modelo Activo</span>
              </div>
            )}
            <button
              onClick={() => loadData(selectedProduct)}
              className="p-2 rounded-xl transition-all hover:bg-white/5"
              title="Refrescar datos"
            >
              <RefreshCw size={18} style={{ color: '#94a3b8' }} />
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Upload Zone */}
        <div
          className={`upload-zone p-6 sm:p-8 mb-6 sm:mb-8 text-center ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".csv,.json"
            className="hidden"
            onChange={handleFileInput}
          />
          <div className="flex flex-col items-center gap-3">
            {uploading ? (
              <div className="spinner" />
            ) : (
              <Upload size={32} style={{ color: '#64748b' }} />
            )}
            <div>
              <p className="text-sm font-medium" style={{ color: '#94a3b8' }}>
                {uploading
                  ? 'Procesando archivo y entrenando modelo...'
                  : 'Arrastra tu archivo CSV o haz clic para seleccionar'}
              </p>
              <p className="text-xs mt-1" style={{ color: '#64748b' }}>
                Columnas: fecha, producto_id, cantidad_vendida, precio, stock_actual
              </p>
            </div>
          </div>
        </div>

        {uploadMessage && (
          <div
            className={`mb-6 p-4 rounded-xl text-sm font-medium ${
              uploadMessage.type === 'success'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {uploadMessage.text}
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-xl text-sm font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            {error}
          </div>
        )}

        {loading && !analytics ? (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <div className="spinner" />
            <p className="text-sm" style={{ color: '#64748b' }}>Cargando datos del dashboard...</p>
          </div>
        ) : analytics ? (
          <>
            {/* ── KPI Cards ── */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6 sm:mb-8">
              <KPICard
                title="Ventas Proyectadas (30d)"
                value={fmt(analytics.kpis.ventas_proyectadas_30d)}
                subtitle="unidades"
                icon={ShoppingCart}
                glowClass="kpi-blue"
                delay={1}
              />
              <KPICard
                title="Ingresos Proyectados"
                value={fmtCurrency(analytics.kpis.ingresos_proyectados_30d)}
                subtitle="próximos 30 días"
                icon={DollarSign}
                glowClass="kpi-emerald"
                delay={2}
              />
              <KPICard
                title="Productos en Riesgo"
                value={analytics.kpis.productos_en_riesgo}
                subtitle="quiebre de stock"
                icon={AlertTriangle}
                glowClass="kpi-rose"
                delay={3}
              />
              <KPICard
                title="Baja Rotación"
                value={analytics.kpis.productos_baja_rotacion}
                subtitle="productos 'hueso'"
                icon={Skull}
                glowClass="kpi-amber"
                delay={4}
              />
              <KPICard
                title="Total Productos"
                value={analytics.kpis.total_productos}
                subtitle="en catálogo"
                icon={Boxes}
                glowClass="kpi-purple"
                delay={5}
              />
              <KPICard
                title="Stock Total"
                value={fmt(analytics.kpis.stock_total)}
                subtitle="unidades"
                icon={Package}
                glowClass="kpi-cyan"
                delay={6}
              />
            </section>

            {/* ── Charts Row ── */}
            <section className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
              {/* Line Chart: Ventas Reales vs Predicción */}
              <div className="glass-card p-6 xl:col-span-2 animate-fade-in-up" style={{ animationDelay: '0.3s', opacity: 0 }}>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0 mb-6">
                  <div>
                    <h2 className="text-base font-semibold" style={{ color: '#f1f5f9' }}>
                      Ventas Reales vs Predicción IA
                    </h2>
                    <p className="text-xs mt-1" style={{ color: '#64748b' }}>
                      Últimos 30 registros del producto seleccionado
                    </p>
                  </div>
                  <select
                    value={selectedProduct || ''}
                    onChange={(e) => setSelectedProduct(e.target.value)}
                    className="w-full sm:w-auto text-sm rounded-xl px-4 py-2 outline-none cursor-pointer"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(148,163,184,0.15)',
                      color: '#f1f5f9',
                    }}
                  >
                    {products.map((p) => (
                      <option key={p} value={p} style={{ background: '#1a2035' }}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>

                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <defs>
                        <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3}/>
                          <stop offset="100%" stopColor="#3b82f6" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="gradPred" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                          <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" vertical={false} />
                      <XAxis
                        dataKey="fecha"
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
                        tickLine={false}
                        tickFormatter={(v) => v.slice(5)}
                      />
                      <YAxis
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend
                        wrapperStyle={{ fontSize: 12, color: '#94a3b8', paddingTop: 12 }}
                      />
                      <Area
                        type="monotone"
                        dataKey="ventas_reales"
                        name="Ventas Reales"
                        stroke="#3b82f6"
                        fill="url(#gradReal)"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 5, fill: '#3b82f6', stroke: '#0a0e1a', strokeWidth: 2 }}
                      />
                      <Area
                        type="monotone"
                        dataKey="prediccion"
                        name="Predicción IA"
                        stroke="#8b5cf6"
                        fill="url(#gradPred)"
                        strokeWidth={2.5}
                        strokeDasharray="6 3"
                        dot={false}
                        activeDot={{ r: 5, fill: '#8b5cf6', stroke: '#0a0e1a', strokeWidth: 2 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[320px] text-sm" style={{ color: '#64748b' }}>
                    Sin datos de comparación disponibles
                  </div>
                )}
              </div>

              {/* Top Products Bar Chart */}
              <div className="glass-card p-6 animate-fade-in-up" style={{ animationDelay: '0.4s', opacity: 0 }}>
                <h2 className="text-base font-semibold mb-1" style={{ color: '#f1f5f9' }}>
                  Top 5 Productos
                </h2>
                <p className="text-xs mb-6" style={{ color: '#64748b' }}>
                  Por volumen total de ventas
                </p>

                {analytics.top_productos?.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart
                      data={analytics.top_productos}
                      layout="vertical"
                      margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" horizontal={false} />
                      <XAxis
                        type="number"
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="producto_id"
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={80}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar
                        dataKey="cantidad_vendida"
                        name="Ventas Totales"
                        fill="url(#barGrad)"
                        radius={[0, 6, 6, 0]}
                        maxBarSize={28}
                      />
                      <defs>
                        <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#3b82f6" />
                          <stop offset="100%" stopColor="#06b6d4" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[280px] text-sm" style={{ color: '#64748b' }}>
                    Sin datos disponibles
                  </div>
                )}
              </div>
            </section>

            {/* ── Inventory Table ── */}
            {inventory && (
              <section className="glass-card overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.5s', opacity: 0 }}>
                <div className="p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0" style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
                  <div>
                    <h2 className="text-base font-semibold" style={{ color: '#f1f5f9' }}>
                      Inventario Inteligente
                    </h2>
                    <p className="text-xs mt-1" style={{ color: '#64748b' }}>
                      {inventory.total_productos} productos ·{' '}
                      <span className="text-rose-400">{inventory.productos_riesgo} en riesgo</span> ·{' '}
                      <span className="text-amber-400">{inventory.productos_baja_rotacion} baja rotación</span> ·{' '}
                      <span className="text-emerald-400">{inventory.productos_saludables} saludables</span>
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Producto</th>
                        <th>Stock Actual</th>
                        <th>Demanda 7d</th>
                        <th>Demanda 30d</th>
                        <th>Stock Crítico</th>
                        <th>Precio Prom.</th>
                        <th>Ventas 30d</th>
                        <th>Estado</th>
                        <th>Detalle</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inventory.inventario.map((item) => (
                        <tr key={item.producto_id}>
                          <td>
                            <span className="font-semibold">{item.producto_id}</span>
                          </td>
                          <td>
                            <span className={`font-mono font-semibold ${
                              item.alerta === 'ROJO' ? 'text-rose-400' :
                              item.alerta === 'AMARILLO' ? 'text-amber-400' :
                              'text-emerald-400'
                            }`}>
                              {fmt(item.stock_actual)}
                            </span>
                          </td>
                          <td className="font-mono">{fmt(item.demanda_predicha_7d, 1)}</td>
                          <td className="font-mono">{fmt(item.demanda_predicha_30d, 1)}</td>
                          <td className="font-mono">{fmt(item.stock_critico, 1)}</td>
                          <td className="font-mono">{fmtCurrency(item.precio_promedio)}</td>
                          <td className="font-mono">{fmt(item.ventas_ultimos_30d)}</td>
                          <td><AlertBadge type={item.alerta} /></td>
                          <td>
                            <span className="text-xs" style={{ color: '#64748b' }}>
                              {item.mensaje_alerta}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* ── Dead Stock Section ── */}
            {analytics?.productos_hueso?.length > 0 && (
              <section className="mt-8 glass-card p-6 animate-fade-in-up" style={{ animationDelay: '0.6s', opacity: 0 }}>
                <h2 className="text-base font-semibold mb-1" style={{ color: '#f1f5f9' }}>
                  🦴 Productos &quot;Hueso&quot; — Baja Rotación
                </h2>
                <p className="text-xs mb-4" style={{ color: '#64748b' }}>
                  Productos sin ventas significativas en los últimos 60 días
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analytics.productos_hueso.map((item) => (
                    <div
                      key={item.producto_id}
                      className="p-4 rounded-xl"
                      style={{
                        background: 'rgba(245, 158, 11, 0.05)',
                        border: '1px solid rgba(245, 158, 11, 0.15)',
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-sm" style={{ color: '#f1f5f9' }}>
                          {item.producto_id}
                        </span>
                        <span className="badge-yellow">
                          {item.dias_sin_ventas_significativas}d sin ventas
                        </span>
                      </div>
                      <p className="text-xs mb-1" style={{ color: '#94a3b8' }}>
                        Stock actual: <strong>{item.stock_actual}</strong> unidades
                        {item.ultima_venta && <> · Última venta: {item.ultima_venta}</>}
                      </p>
                      <p className="text-xs" style={{ color: '#fbbf24' }}>
                        {item.recomendacion}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        ) : (
          /* ── Empty State ── */
          <div className="flex flex-col items-center justify-center py-16 sm:py-32 gap-6 text-center px-4">
            <div
              className="p-6 rounded-2xl"
              style={{ background: 'rgba(59, 130, 246, 0.1)' }}
            >
              <BarChart3 size={48} style={{ color: '#3b82f6' }} />
            </div>
            <div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: '#f1f5f9' }}>
                Comienza subiendo tus datos
              </h2>
              <p className="text-sm max-w-md" style={{ color: '#64748b' }}>
                Arrastra un archivo CSV con tu historial de ventas para que la IA
                analice tu inventario y genere predicciones de demanda.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer
        className="text-center py-6"
        style={{ borderTop: '1px solid rgba(148,163,184,0.06)' }}
      >
        <p className="text-xs" style={{ color: '#475569' }}>
          PredictStock AI v1.0 · Powered by RandomForest ML Engine · {new Date().getFullYear()}
        </p>
      </footer>
    </div>
  );
}
