import React, { useEffect, useState, useRef } from 'react';
import { Layout } from '../../components/shared/Layout';
import { adminAPI } from '../../services/api';
import {
  Truck, MapPin, Users, CheckCircle, Upload,
  FileText, Calendar, Pill, TestTube, Heart, Search, Plus, X,
  Download, Eye, Edit2, Trash2, Stethoscope, Activity, Loader2
} from 'lucide-react';

interface HealthRecord {
  id: number;
  user_id: string;
  user_name: string;
  type: 'appointment' | 'test_result' | 'medication' | 'consultation';
  title: string;
  date: string;
  status: string;
  provider?: string;
  details?: string;
}

export const MAWDYDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [_loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'health' | 'appointments' | 'results' | 'medications'>('overview');

  // Health Records State
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  // CSV Import State
  const [showImportModal, setShowImportModal] = useState(false);
  const [importType, setImportType] = useState<'appointments' | 'results' | 'medications'>('appointments');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importPreview, setImportPreview] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Manual Entry Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [addType, setAddType] = useState<'appointment' | 'result' | 'medication'>('appointment');
  const [addForm, setAddForm] = useState({
    user_id: '',
    title: '',
    date: '',
    provider: '',
    details: '',
    status: 'scheduled'
  });
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    loadDashboard();
    loadHealthRecords();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await adminAPI.getMAWDYOverview();
      setData(response.data);
    } catch (error) {
      console.error('Failed to load MAWDY dashboard:', error);
      // Set demo data
      setData({
        total_techs: 15,
        online_techs: 8,
        active_jobs: 12,
        jobs_today: 24,
        total_health_users: 150,
        appointments_this_month: 45,
        recent_jobs: []
      });
    } finally {
      setLoading(false);
    }
  };

  const loadHealthRecords = async () => {
    // Demo data - in production this would come from API
    setHealthRecords([
      { id: 1, user_id: 'PAQ-30082653', user_name: 'Juan Perez', type: 'appointment', title: 'Consulta General', date: '2024-12-01', status: 'scheduled', provider: 'Dr. Maria Garcia' },
      { id: 2, user_id: 'PAQ-30082654', user_name: 'Ana Lopez', type: 'test_result', title: 'Examen de Sangre', date: '2024-11-28', status: 'completed', provider: 'Laboratorio Central' },
      { id: 3, user_id: 'PAQ-30082655', user_name: 'Carlos Rodriguez', type: 'medication', title: 'Paracetamol 500mg', date: '2024-11-27', status: 'delivered', details: 'Entregado a domicilio' },
    ]);
  };

  // Handle CSV file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCsvFile(file);
      parseCSVPreview(file);
    }
  };

  // Parse CSV for preview
  const parseCSVPreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n');
      const headers = lines[0].split(',').map(h => h.trim());
      const preview = lines.slice(1, 6).map(line => {
        const values = line.split(',');
        const obj: any = {};
        headers.forEach((header, i) => {
          obj[header] = values[i]?.trim();
        });
        return obj;
      }).filter(obj => Object.values(obj).some(v => v));
      setImportPreview(preview);
    };
    reader.readAsText(file);
  };

  // Handle CSV Import
  const handleImport = async () => {
    if (!csvFile) return;

    setImporting(true);
    try {
      // In production, this would upload to API
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Add imported records to local state
      const newRecords: HealthRecord[] = importPreview.map((item, idx) => ({
        id: Date.now() + idx,
        user_id: item.user_id || item.paq_id || 'PAQ-UNKNOWN',
        user_name: item.user_name || item.nombre || 'Usuario',
        type: importType === 'appointments' ? 'appointment' : importType === 'results' ? 'test_result' : 'medication',
        title: item.title || item.titulo || item.descripcion || 'Sin titulo',
        date: item.date || item.fecha || new Date().toISOString().split('T')[0],
        status: item.status || 'pending',
        provider: item.provider || item.proveedor,
        details: item.details || item.detalles
      }));

      setHealthRecords([...newRecords, ...healthRecords]);
      setShowImportModal(false);
      setCsvFile(null);
      setImportPreview([]);
      alert(`Se importaron ${newRecords.length} registros exitosamente`);
    } catch (error) {
      alert('Error al importar archivo CSV');
    } finally {
      setImporting(false);
    }
  };

  // Handle manual add
  const handleAdd = async () => {
    if (!addForm.user_id || !addForm.title || !addForm.date) {
      alert('Por favor completa los campos requeridos');
      return;
    }

    setAddLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newRecord: HealthRecord = {
        id: Date.now(),
        user_id: addForm.user_id,
        user_name: 'Usuario PAQ', // In production, fetch user name
        type: addType === 'appointment' ? 'appointment' : addType === 'result' ? 'test_result' : 'medication',
        title: addForm.title,
        date: addForm.date,
        status: addForm.status,
        provider: addForm.provider,
        details: addForm.details
      };

      setHealthRecords([newRecord, ...healthRecords]);
      setShowAddModal(false);
      setAddForm({ user_id: '', title: '', date: '', provider: '', details: '', status: 'scheduled' });
      alert('Registro agregado exitosamente');
    } catch (error) {
      alert('Error al agregar registro');
    } finally {
      setAddLoading(false);
    }
  };

  // Delete record
  const handleDelete = (id: number) => {
    if (confirm('¿Estás seguro de eliminar este registro?')) {
      setHealthRecords(healthRecords.filter(r => r.id !== id));
    }
  };

  // Filter records
  const filteredRecords = healthRecords.filter(record => {
    const matchesSearch = searchQuery === '' ||
      record.user_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.title.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType = filterType === 'all' || record.type === filterType;

    return matchesSearch && matchesType;
  });

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      scheduled: { color: 'bg-blue-100 text-blue-700', label: 'Programado' },
      completed: { color: 'bg-green-100 text-green-700', label: 'Completado' },
      pending: { color: 'bg-yellow-100 text-yellow-700', label: 'Pendiente' },
      delivered: { color: 'bg-green-100 text-green-700', label: 'Entregado' },
      cancelled: { color: 'bg-red-100 text-red-700', label: 'Cancelado' },
    };
    const config = configs[status] || { color: 'bg-gray-100 text-gray-700', label: status };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>{config.label}</span>;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'appointment': return <Calendar className="text-blue-500" size={18} />;
      case 'test_result': return <TestTube className="text-purple-500" size={18} />;
      case 'medication': return <Pill className="text-green-500" size={18} />;
      case 'consultation': return <Stethoscope className="text-pink-500" size={18} />;
      default: return <FileText className="text-gray-500" size={18} />;
    }
  };

  return (
    <Layout variant="mawdy-admin">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MAWDY Dashboard</h1>
            <p className="text-gray-500">Administracion de tecnicos, servicios y datos de salud</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowImportModal(true)}
              className="btn btn-outline flex items-center gap-2"
            >
              <Upload size={18} />
              Importar CSV
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn btn-primary flex items-center gap-2"
            >
              <Plus size={18} />
              Agregar Registro
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200 overflow-x-auto">
          {[
            { id: 'overview', label: 'Vista General', icon: Activity },
            { id: 'health', label: 'Registros de Salud', icon: Heart },
            { id: 'appointments', label: 'Citas', icon: Calendar },
            { id: 'results', label: 'Resultados', icon: TestTube },
            { id: 'medications', label: 'Medicamentos', icon: Pill }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="card bg-gradient-to-br from-red-500 to-red-600 text-white">
                <div className="flex items-center gap-4">
                  <Users size={32} className="opacity-80" />
                  <div>
                    <p className="text-3xl font-bold">{data?.total_techs || 0}</p>
                    <p className="text-red-100">Tecnicos Totales</p>
                  </div>
                </div>
              </div>
              <div className="card bg-gradient-to-br from-green-500 to-green-600 text-white">
                <div className="flex items-center gap-4">
                  <CheckCircle size={32} className="opacity-80" />
                  <div>
                    <p className="text-3xl font-bold">{data?.online_techs || 0}</p>
                    <p className="text-green-100">En Linea</p>
                  </div>
                </div>
              </div>
              <div className="card bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                <div className="flex items-center gap-4">
                  <Truck size={32} className="opacity-80" />
                  <div>
                    <p className="text-3xl font-bold">{data?.active_jobs || 0}</p>
                    <p className="text-orange-100">Trabajos Activos</p>
                  </div>
                </div>
              </div>
              <div className="card bg-gradient-to-br from-pink-500 to-pink-600 text-white">
                <div className="flex items-center gap-4">
                  <Heart size={32} className="opacity-80" />
                  <div>
                    <p className="text-3xl font-bold">{data?.total_health_users || healthRecords.length}</p>
                    <p className="text-pink-100">Registros Salud</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Map Placeholder */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MapPin className="text-red-500" />
                Mapa de Tecnicos en Vivo
              </h3>
              <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <MapPin size={48} className="mx-auto mb-2 opacity-50" />
                  <p>El mapa en vivo se mostrara aqui</p>
                  <p className="text-sm">Integracion con Google Maps API</p>
                </div>
              </div>
            </div>

            {/* Active Jobs Table */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Trabajos Activos</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium text-gray-600">Numero</th>
                      <th className="text-left p-3 font-medium text-gray-600">Tipo</th>
                      <th className="text-left p-3 font-medium text-gray-600">Tecnico</th>
                      <th className="text-left p-3 font-medium text-gray-600">Estado</th>
                      <th className="text-left p-3 font-medium text-gray-600">Ubicacion</th>
                      <th className="text-left p-3 font-medium text-gray-600">ETA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.recent_jobs?.length > 0 ? (
                      data.recent_jobs.map((job: any) => (
                        <tr key={job.id} className="border-b hover:bg-gray-50">
                          <td className="p-3 font-medium">{job.request_number}</td>
                          <td className="p-3">{job.service_type}</td>
                          <td className="p-3">{job.tech_name}</td>
                          <td className="p-3">{getStatusBadge(job.status)}</td>
                          <td className="p-3">{job.location}</td>
                          <td className="p-3">{job.eta || '-'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-gray-500">
                          No hay trabajos activos
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Health Records Tab */}
        {(activeTab === 'health' || activeTab === 'appointments' || activeTab === 'results' || activeTab === 'medications') && (
          <>
            {/* Search and Filter */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Buscar por usuario, ID o titulo..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                />
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500"
              >
                <option value="all">Todos los tipos</option>
                <option value="appointment">Citas</option>
                <option value="test_result">Resultados</option>
                <option value="medication">Medicamentos</option>
              </select>
              <button className="btn btn-outline flex items-center gap-2">
                <Download size={18} />
                Exportar
              </button>
            </div>

            {/* Records Table */}
            <div className="card">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium text-gray-600">Tipo</th>
                      <th className="text-left p-3 font-medium text-gray-600">Usuario</th>
                      <th className="text-left p-3 font-medium text-gray-600">ID PAQ</th>
                      <th className="text-left p-3 font-medium text-gray-600">Titulo</th>
                      <th className="text-left p-3 font-medium text-gray-600">Fecha</th>
                      <th className="text-left p-3 font-medium text-gray-600">Proveedor</th>
                      <th className="text-left p-3 font-medium text-gray-600">Estado</th>
                      <th className="text-left p-3 font-medium text-gray-600">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.length > 0 ? (
                      filteredRecords
                        .filter(record => {
                          if (activeTab === 'appointments') return record.type === 'appointment';
                          if (activeTab === 'results') return record.type === 'test_result';
                          if (activeTab === 'medications') return record.type === 'medication';
                          return true;
                        })
                        .map((record) => (
                          <tr key={record.id} className="border-b hover:bg-gray-50">
                            <td className="p-3">{getTypeIcon(record.type)}</td>
                            <td className="p-3 font-medium">{record.user_name}</td>
                            <td className="p-3 text-sm text-gray-500">{record.user_id}</td>
                            <td className="p-3">{record.title}</td>
                            <td className="p-3">{new Date(record.date).toLocaleDateString('es-GT')}</td>
                            <td className="p-3">{record.provider || '-'}</td>
                            <td className="p-3">{getStatusBadge(record.status)}</td>
                            <td className="p-3">
                              <div className="flex gap-2">
                                <button className="p-1 hover:bg-gray-100 rounded">
                                  <Eye size={16} className="text-gray-500" />
                                </button>
                                <button className="p-1 hover:bg-gray-100 rounded">
                                  <Edit2 size={16} className="text-blue-500" />
                                </button>
                                <button
                                  onClick={() => handleDelete(record.id)}
                                  className="p-1 hover:bg-gray-100 rounded"
                                >
                                  <Trash2 size={16} className="text-red-500" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                    ) : (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-gray-500">
                          No hay registros que coincidan con la busqueda
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Import CSV Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">Importar Datos CSV</h3>
                <button
                  onClick={() => { setShowImportModal(false); setCsvFile(null); setImportPreview([]); }}
                  className="p-2 hover:bg-gray-100 rounded-full"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Import Type Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Datos a Importar
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'appointments', label: 'Citas', icon: Calendar },
                    { id: 'results', label: 'Resultados', icon: TestTube },
                    { id: 'medications', label: 'Medicamentos', icon: Pill }
                  ].map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setImportType(type.id as any)}
                      className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                        importType === type.id
                          ? 'border-red-500 bg-red-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <type.icon size={24} className={importType === type.id ? 'text-red-500' : 'text-gray-400'} />
                      <span className={importType === type.id ? 'text-red-700 font-medium' : 'text-gray-600'}>
                        {type.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* File Upload */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Archivo CSV
                </label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-red-400 transition-colors"
                >
                  {csvFile ? (
                    <div>
                      <FileText size={48} className="mx-auto mb-2 text-green-500" />
                      <p className="font-medium text-gray-900">{csvFile.name}</p>
                      <p className="text-sm text-gray-500">{(csvFile.size / 1024).toFixed(2)} KB</p>
                    </div>
                  ) : (
                    <div>
                      <Upload size={48} className="mx-auto mb-2 text-gray-400" />
                      <p className="text-gray-600">Haz clic o arrastra un archivo CSV</p>
                      <p className="text-sm text-gray-400 mt-1">Maximo 5MB</p>
                    </div>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {/* CSV Format Guide */}
              <div className="mb-6 p-4 bg-blue-50 rounded-xl">
                <h4 className="font-medium text-blue-900 mb-2">Formato del CSV</h4>
                <p className="text-sm text-blue-700">
                  El archivo debe incluir las columnas: <code className="bg-blue-100 px-1 rounded">user_id</code>, <code className="bg-blue-100 px-1 rounded">title</code>, <code className="bg-blue-100 px-1 rounded">date</code>, <code className="bg-blue-100 px-1 rounded">status</code>
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Columnas opcionales: provider, details, user_name
                </p>
              </div>

              {/* Preview */}
              {importPreview.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-2">Vista Previa ({importPreview.length} registros)</h4>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(importPreview[0]).map((key) => (
                            <th key={key} className="p-2 text-left font-medium text-gray-600">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.map((row, idx) => (
                          <tr key={idx} className="border-t">
                            {Object.values(row).map((val: any, i) => (
                              <td key={i} className="p-2 text-gray-700">
                                {val || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => { setShowImportModal(false); setCsvFile(null); setImportPreview([]); }}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleImport}
                  disabled={!csvFile || importing}
                  className="flex-1 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-bold rounded-xl hover:from-red-600 hover:to-red-700 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {importing ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Importando...
                    </>
                  ) : (
                    <>
                      <Upload size={20} />
                      Importar Datos
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Record Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">Agregar Registro</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-full"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Type Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'appointment', label: 'Cita', icon: Calendar },
                    { id: 'result', label: 'Resultado', icon: TestTube },
                    { id: 'medication', label: 'Medicamento', icon: Pill }
                  ].map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setAddType(type.id as any)}
                      className={`p-3 rounded-lg border-2 transition-all flex flex-col items-center gap-1 ${
                        addType === type.id
                          ? 'border-red-500 bg-red-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <type.icon size={20} className={addType === type.id ? 'text-red-500' : 'text-gray-400'} />
                      <span className="text-xs">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID PAQ *</label>
                  <input
                    type="text"
                    value={addForm.user_id}
                    onChange={(e) => setAddForm({ ...addForm, user_id: e.target.value })}
                    placeholder="PAQ-12345678"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Titulo *</label>
                  <input
                    type="text"
                    value={addForm.title}
                    onChange={(e) => setAddForm({ ...addForm, title: e.target.value })}
                    placeholder="Descripcion del registro"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha *</label>
                  <input
                    type="date"
                    value={addForm.date}
                    onChange={(e) => setAddForm({ ...addForm, date: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Proveedor</label>
                  <input
                    type="text"
                    value={addForm.provider}
                    onChange={(e) => setAddForm({ ...addForm, provider: e.target.value })}
                    placeholder="Nombre del doctor o laboratorio"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Detalles</label>
                  <textarea
                    value={addForm.details}
                    onChange={(e) => setAddForm({ ...addForm, details: e.target.value })}
                    placeholder="Informacion adicional"
                    rows={2}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={addForm.status}
                    onChange={(e) => setAddForm({ ...addForm, status: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-red-500"
                  >
                    <option value="scheduled">Programado</option>
                    <option value="pending">Pendiente</option>
                    <option value="completed">Completado</option>
                    <option value="delivered">Entregado</option>
                    <option value="cancelled">Cancelado</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAdd}
                  disabled={addLoading}
                  className="flex-1 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-bold rounded-xl hover:from-red-600 hover:to-red-700 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {addLoading ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <Plus size={20} />
                      Agregar
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};
