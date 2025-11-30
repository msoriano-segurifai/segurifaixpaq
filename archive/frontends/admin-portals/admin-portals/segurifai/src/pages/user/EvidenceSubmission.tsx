import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../../components/shared/Layout';
import { documentAPI, evidenceAPI } from '../../services/api';
import {
  Camera, FileText, Upload, CheckCircle, AlertCircle, XCircle,
  RefreshCw, Sparkles, Shield, Eye, Trash2, Plus, ChevronRight,
  Car, Heart, Wrench, AlertTriangle, Clock, Send
} from 'lucide-react';

interface RequiredDocument {
  type: string;
  required: boolean;
  description: string;
  uploaded: boolean;
  approved: boolean;
  document_id: number | null;
  review_status: string | null;
  review_notes: string | null;
}

interface UploadedDocument {
  id: number;
  document_type: string;
  original_filename: string;
  review_status: string;
  ai_confidence_score: number;
  ai_review_notes: string;
  ai_detected_issues: string[];
  uploaded_at: string;
}

interface EvidenceForm {
  id: number;
  form_type: string;
  status: string;
  incident_description: string;
  created_at: string;
}

export const EvidenceSubmission: React.FC = () => {
  const { requestId } = useParams<{ requestId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [requiredDocs, setRequiredDocs] = useState<RequiredDocument[]>([]);
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([]);
  const [evidenceOptions, setEvidenceOptions] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'photos' | 'form'>('photos');
  const [selectedDocType, setSelectedDocType] = useState<string>('');
  const [showFormModal, setShowFormModal] = useState(false);
  const [formData, setFormData] = useState<any>({});
  const [submittingForm, setSubmittingForm] = useState(false);
  const [formId, setFormId] = useState<number | null>(null);

  useEffect(() => {
    if (requestId) {
      loadEvidenceData();
    }
  }, [requestId]);

  const loadEvidenceData = async () => {
    try {
      const [optionsRes, docsRes, requiredRes] = await Promise.all([
        evidenceAPI.getEvidenceOptions(parseInt(requestId!)),
        documentAPI.getRequestDocuments(parseInt(requestId!)),
        documentAPI.getRequiredDocuments(parseInt(requestId!))
      ]);

      setEvidenceOptions(optionsRes.data);
      setUploadedDocs(docsRes.data.documents || []);
      setRequiredDocs(requiredRes.data.documents || []);

      // Auto-select form tab for health assistance
      if (optionsRes.data.assistance_type === 'HEALTH') {
        setActiveTab('form');
      }
    } catch (error) {
      console.error('Error cargando datos de evidencia:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedDocType) return;

    setUploading(true);
    try {
      const response = await documentAPI.uploadDocument(
        parseInt(requestId!),
        selectedDocType,
        file
      );

      // Show AI review result
      const review = response.data.review;
      if (review.status === 'APPROVED') {
        alert(`Documento aprobado automaticamente por IA. Confianza: ${(review.confidence * 100).toFixed(0)}%`);
      } else if (review.status === 'NEEDS_RESUBMIT') {
        alert(`El documento necesita ser reenviado: ${review.notes}`);
      } else {
        alert(`Documento en revision. Estado: ${review.status}`);
      }

      await loadEvidenceData();
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al subir documento');
    } finally {
      setUploading(false);
      setSelectedDocType('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleUploadClick = (docType: string) => {
    setSelectedDocType(docType);
    fileInputRef.current?.click();
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('¿Estas seguro de eliminar este documento?')) return;

    try {
      await documentAPI.deleteDocument(docId);
      await loadEvidenceData();
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al eliminar documento');
    }
  };

  const getFormType = () => {
    if (evidenceOptions?.assistance_type === 'HEALTH') return 'HEALTH_INCIDENT';
    if (evidenceOptions?.assistance_type === 'ROADSIDE') return 'ROADSIDE_ISSUE';
    return 'VEHICLE_DAMAGE';
  };

  const handleCreateForm = async () => {
    setSubmittingForm(true);
    try {
      const response = await evidenceAPI.createEvidenceForm({
        request_id: parseInt(requestId!),
        form_type: getFormType(),
        ...formData
      });
      setFormId(response.data.form_id);
      alert('Formulario creado. Complete todos los campos requeridos.');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al crear formulario');
    } finally {
      setSubmittingForm(false);
    }
  };

  const handleSubmitForm = async () => {
    if (!formId) return;
    setSubmittingForm(true);
    try {
      // First update the form with current data
      await evidenceAPI.updateEvidenceForm(formId, formData);

      // Then submit for AI review
      const response = await evidenceAPI.submitEvidenceForm(formId, true);

      if (response.data.status === 'APPROVED') {
        alert('Formulario aprobado automaticamente por IA');
        navigate(`/app/requests/${requestId}`);
      } else if (response.data.status === 'NEEDS_INFO') {
        alert(`Se requiere informacion adicional: ${response.data.issues?.join(', ')}`);
      } else {
        alert('Formulario enviado para revision por agente MAWDY');
        navigate(`/app/requests/${requestId}`);
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Error al enviar formulario');
    } finally {
      setSubmittingForm(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'REJECTED':
        return <XCircle className="text-red-500" size={20} />;
      case 'NEEDS_RESUBMIT':
        return <AlertCircle className="text-orange-500" size={20} />;
      case 'REVIEWING':
        return <RefreshCw className="text-blue-500 animate-spin" size={20} />;
      default:
        return <Clock className="text-gray-400" size={20} />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      APPROVED: 'Aprobado',
      REJECTED: 'Rechazado',
      NEEDS_RESUBMIT: 'Reenviar',
      REVIEWING: 'Revisando',
      PENDING: 'Pendiente'
    };
    return labels[status] || status;
  };

  if (loading) {
    return (
      <Layout variant="user">
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="animate-spin text-blue-600" size={48} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout variant="user">
      <div className="max-w-3xl mx-auto space-y-6 pb-8">
        {/* Header */}
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="text-blue-600" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Enviar Evidencia</h1>
          <p className="text-gray-500 mt-1">
            Nuestro sistema de IA revisara tu evidencia automaticamente
          </p>
        </div>

        {/* AI Info Banner */}
        <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Sparkles className="text-purple-600" size={24} />
            </div>
            <div>
              <h3 className="font-bold text-purple-900">Revision Automatica con IA</h3>
              <p className="text-sm text-purple-700 mt-1">
                Tus documentos seran analizados por inteligencia artificial para agilizar el proceso.
                Si la IA no puede verificar la evidencia, un agente MAWDY la revisara manualmente.
              </p>
            </div>
          </div>
        </div>

        {/* Evidence Type Tabs */}
        <div className="flex bg-gray-100 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('photos')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'photos'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Camera size={18} />
            Fotos/Documentos
          </button>
          <button
            onClick={() => setActiveTab('form')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'form'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText size={18} />
            Formulario
          </button>
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Photos/Documents Tab */}
        {activeTab === 'photos' && (
          <div className="space-y-4">
            {/* Required Documents */}
            <div className="card">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Camera size={18} />
                Documentos Requeridos
              </h3>
              <div className="space-y-3">
                {requiredDocs.map((doc) => (
                  <div
                    key={doc.type}
                    className={`p-4 rounded-xl border-2 ${
                      doc.approved
                        ? 'border-green-300 bg-green-50'
                        : doc.uploaded
                        ? 'border-yellow-300 bg-yellow-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {doc.approved ? (
                          <CheckCircle className="text-green-500" size={24} />
                        ) : doc.uploaded ? (
                          <AlertCircle className="text-yellow-500" size={24} />
                        ) : (
                          <div className="w-6 h-6 border-2 border-gray-300 rounded-full" />
                        )}
                        <div>
                          <p className="font-medium">{doc.description}</p>
                          <p className="text-xs text-gray-500">
                            {doc.required ? 'Requerido' : 'Opcional'}
                          </p>
                        </div>
                      </div>
                      {!doc.approved && (
                        <button
                          onClick={() => handleUploadClick(doc.type)}
                          disabled={uploading}
                          className="btn btn-primary btn-sm flex items-center gap-1"
                        >
                          {uploading && selectedDocType === doc.type ? (
                            <RefreshCw className="animate-spin" size={14} />
                          ) : (
                            <Upload size={14} />
                          )}
                          {doc.uploaded ? 'Reenviar' : 'Subir'}
                        </button>
                      )}
                    </div>
                    {doc.review_notes && (
                      <p className="mt-2 text-sm text-orange-600 bg-orange-100 p-2 rounded">
                        {doc.review_notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Uploaded Documents */}
            {uploadedDocs.length > 0 && (
              <div className="card">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <Eye size={18} />
                  Documentos Subidos
                </h3>
                <div className="space-y-3">
                  {uploadedDocs.map((doc) => (
                    <div key={doc.id} className="p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(doc.review_status)}
                          <div>
                            <p className="font-medium">{doc.original_filename}</p>
                            <p className="text-xs text-gray-500">{doc.document_type}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            doc.review_status === 'APPROVED'
                              ? 'bg-green-100 text-green-700'
                              : doc.review_status === 'REJECTED'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {getStatusLabel(doc.review_status)}
                          </span>
                          {doc.review_status !== 'APPROVED' && (
                            <button
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="p-1 text-red-500 hover:bg-red-50 rounded"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* AI Review Info */}
                      {doc.ai_confidence_score > 0 && (
                        <div className="mt-2 p-2 bg-purple-50 rounded-lg">
                          <div className="flex items-center gap-2 text-sm text-purple-700">
                            <Sparkles size={14} />
                            <span>Confianza IA: {(doc.ai_confidence_score * 100).toFixed(0)}%</span>
                          </div>
                          {doc.ai_review_notes && (
                            <p className="text-xs text-purple-600 mt-1">{doc.ai_review_notes}</p>
                          )}
                        </div>
                      )}

                      {/* Issues */}
                      {doc.ai_detected_issues && doc.ai_detected_issues.length > 0 && (
                        <div className="mt-2">
                          {doc.ai_detected_issues.map((issue, i) => (
                            <p key={i} className="text-xs text-red-600 flex items-center gap-1">
                              <AlertTriangle size={12} />
                              {issue}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Form Tab */}
        {activeTab === 'form' && (
          <div className="card">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <FileText size={18} />
              Formulario de Evidencia
              {evidenceOptions?.assistance_type === 'HEALTH' && (
                <span className="ml-2 px-2 py-1 bg-pink-100 text-pink-700 text-xs rounded-full">
                  Salud
                </span>
              )}
            </h3>

            <div className="space-y-4">
              {/* Common Fields */}
              <div>
                <label className="label">Descripcion del Incidente *</label>
                <textarea
                  value={formData.incident_description || ''}
                  onChange={(e) => setFormData({ ...formData, incident_description: e.target.value })}
                  className="input min-h-[100px]"
                  placeholder="Describe detalladamente lo que ocurrio..."
                />
              </div>

              <div>
                <label className="label">Ubicacion del Incidente</label>
                <input
                  type="text"
                  value={formData.location_description || ''}
                  onChange={(e) => setFormData({ ...formData, location_description: e.target.value })}
                  className="input"
                  placeholder="Ej: Zona 10, frente al centro comercial..."
                />
              </div>

              {/* Vehicle Fields (for roadside/vehicle) */}
              {(evidenceOptions?.assistance_type === 'ROADSIDE' ||
                evidenceOptions?.assistance_type === 'VEHICULAR') && (
                <>
                  <div className="border-t pt-4 mt-4">
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Car size={16} />
                      Informacion del Vehiculo
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="label">Marca</label>
                        <input
                          type="text"
                          value={formData.vehicle_make || ''}
                          onChange={(e) => setFormData({ ...formData, vehicle_make: e.target.value })}
                          className="input"
                          placeholder="Toyota"
                        />
                      </div>
                      <div>
                        <label className="label">Modelo</label>
                        <input
                          type="text"
                          value={formData.vehicle_model || ''}
                          onChange={(e) => setFormData({ ...formData, vehicle_model: e.target.value })}
                          className="input"
                          placeholder="Corolla"
                        />
                      </div>
                      <div>
                        <label className="label">Ano</label>
                        <input
                          type="number"
                          value={formData.vehicle_year || ''}
                          onChange={(e) => setFormData({ ...formData, vehicle_year: e.target.value })}
                          className="input"
                          placeholder="2020"
                        />
                      </div>
                      <div>
                        <label className="label">Placa</label>
                        <input
                          type="text"
                          value={formData.vehicle_plate || ''}
                          onChange={(e) => setFormData({ ...formData, vehicle_plate: e.target.value })}
                          className="input"
                          placeholder="P-123ABC"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="label">Descripcion del Dano</label>
                    <textarea
                      value={formData.damage_description || ''}
                      onChange={(e) => setFormData({ ...formData, damage_description: e.target.value })}
                      className="input min-h-[80px]"
                      placeholder="Describe los danos visibles..."
                    />
                  </div>

                  <div>
                    <label className="label">Tipo de Problema</label>
                    <select
                      value={formData.issue_type || ''}
                      onChange={(e) => setFormData({ ...formData, issue_type: e.target.value })}
                      className="input"
                    >
                      <option value="">Seleccionar...</option>
                      <option value="FLAT_TIRE">Llanta Ponchada</option>
                      <option value="BATTERY">Bateria Descargada</option>
                      <option value="FUEL">Sin Combustible</option>
                      <option value="LOCKOUT">Llaves Dentro</option>
                      <option value="ACCIDENT">Accidente</option>
                      <option value="MECHANICAL">Falla Mecanica</option>
                      <option value="OTHER">Otro</option>
                    </select>
                  </div>
                </>
              )}

              {/* Health Fields */}
              {evidenceOptions?.assistance_type === 'HEALTH' && (
                <>
                  <div className="border-t pt-4 mt-4">
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Heart size={16} />
                      Informacion Medica
                    </h4>
                  </div>

                  <div>
                    <label className="label">Sintomas Actuales *</label>
                    <textarea
                      value={formData.symptoms_description || ''}
                      onChange={(e) => setFormData({ ...formData, symptoms_description: e.target.value })}
                      className="input min-h-[80px]"
                      placeholder="Describe tus sintomas actuales..."
                    />
                  </div>

                  <div>
                    <label className="label">Historial Medico Relevante</label>
                    <textarea
                      value={formData.medical_history || ''}
                      onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                      className="input min-h-[60px]"
                      placeholder="Condiciones medicas previas, cirugias, etc..."
                    />
                  </div>

                  <div>
                    <label className="label">Medicamentos Actuales</label>
                    <input
                      type="text"
                      value={formData.current_medications || ''}
                      onChange={(e) => setFormData({ ...formData, current_medications: e.target.value })}
                      className="input"
                      placeholder="Lista de medicamentos que tomas actualmente"
                    />
                  </div>

                  <div>
                    <label className="label">Alergias</label>
                    <input
                      type="text"
                      value={formData.allergies || ''}
                      onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
                      className="input"
                      placeholder="Alergias conocidas a medicamentos u otros"
                    />
                  </div>
                </>
              )}

              {/* Witness Info */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium mb-3">Testigo (Opcional)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Nombre</label>
                    <input
                      type="text"
                      value={formData.witness_name || ''}
                      onChange={(e) => setFormData({ ...formData, witness_name: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">Telefono</label>
                    <input
                      type="tel"
                      value={formData.witness_phone || ''}
                      onChange={(e) => setFormData({ ...formData, witness_phone: e.target.value })}
                      className="input"
                    />
                  </div>
                </div>
              </div>

              {/* Declaration */}
              <div className="p-4 bg-gray-50 rounded-xl">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.declaration_accepted || false}
                    onChange={(e) => setFormData({ ...formData, declaration_accepted: e.target.checked })}
                    className="mt-1"
                  />
                  <span className="text-sm text-gray-600">
                    Declaro que la informacion proporcionada es veridica y me comprometo
                    a que cualquier falsedad puede resultar en la cancelacion del servicio.
                  </span>
                </label>
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3">
                {!formId ? (
                  <button
                    onClick={handleCreateForm}
                    disabled={submittingForm || !formData.incident_description}
                    className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                  >
                    {submittingForm ? (
                      <RefreshCw className="animate-spin" size={18} />
                    ) : (
                      <Plus size={18} />
                    )}
                    Crear Formulario
                  </button>
                ) : (
                  <button
                    onClick={handleSubmitForm}
                    disabled={submittingForm || !formData.declaration_accepted}
                    className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                  >
                    {submittingForm ? (
                      <RefreshCw className="animate-spin" size={18} />
                    ) : (
                      <Send size={18} />
                    )}
                    Enviar para Revision IA
                  </button>
                )}
              </div>

              {/* AI Review Info */}
              <div className="text-center text-sm text-gray-500">
                <Sparkles className="inline mr-1" size={14} />
                Tu formulario sera analizado automaticamente por IA
              </div>
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="text-center text-sm text-gray-500">
          <p>¿Necesitas ayuda? Contactanos al</p>
          <a href="tel:+50212345678" className="text-blue-600 font-medium">
            +502 1234 5678
          </a>
        </div>
      </div>
    </Layout>
  );
};
