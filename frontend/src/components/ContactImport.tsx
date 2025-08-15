import React, { useState, useRef } from 'react';
import * as XLSX from 'xlsx';
import { contactService } from '../services/contactService';
import type { ContactCreateRequest } from '../services/contactService';

interface ImportResult {
  success: number;
  errors: string[];
  duplicates: string[];
  total: number;
}

interface ContactPreview {
  contact: ContactCreateRequest;
  status: 'valid' | 'duplicate' | 'error';
  error?: string;
}

interface ContactImportProps {
  onImportComplete?: () => void;
  onClose?: () => void;
}

const ContactImport: React.FC<ContactImportProps> = ({ onImportComplete, onClose }) => {
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [contactPreview, setContactPreview] = useState<ContactPreview[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Función para formatear número de teléfono según estándar de WhatsApp
  const formatPhoneNumber = (phone: string): string => {
    // Asegurar que phone sea una cadena de texto
    const phoneStr = String(phone || '');
    
    // Remover todos los caracteres no numéricos
    let cleaned = phoneStr.replace(/\D/g, '');
    
    // Si está vacío después de limpiar, es inválido
    if (!cleaned || cleaned.length === 0) {
      throw new Error('Número de teléfono inválido - campo vacío');
    }
    
    // Detectar y formatear diferentes formatos comunes
    let formattedNumber = '';
    
    // Caso 1: Ya tiene código de país (57XXXXXXXXX)
    if (cleaned.startsWith('57') && cleaned.length === 12) {
      formattedNumber = cleaned;
    }
    // Caso 2: Número colombiano de 10 dígitos (3XXXXXXXXX)
    else if (cleaned.length === 10 && cleaned.startsWith('3')) {
      formattedNumber = '57' + cleaned;
    }
    // Caso 3: Número con 0 al inicio (03XXXXXXXXX)
    else if (cleaned.length === 11 && cleaned.startsWith('03')) {
      formattedNumber = '57' + cleaned.substring(1);
    }
    // Caso 4: Número con código de país sin 57 (57XXXXXXXXX pero sin 57)
    else if (cleaned.length === 8) {
      formattedNumber = '57' + cleaned;
    }
    // Caso 5: Número con formato internacional (+57XXXXXXXXX)
    else if (cleaned.startsWith('57') && cleaned.length > 12) {
      // Tomar solo los primeros 12 dígitos
      formattedNumber = cleaned.substring(0, 12);
    }
    // Caso 6: Otros formatos - intentar formatear
    else {
      // Si empieza con 0, removerlo
      if (cleaned.startsWith('0')) {
        cleaned = cleaned.substring(1);
      }
      
      // Si no empieza con 57, agregarlo
      if (!cleaned.startsWith('57')) {
        cleaned = '57' + cleaned;
      }
      
      // Asegurar que tenga exactamente 12 dígitos
      if (cleaned.length > 12) {
        cleaned = cleaned.substring(0, 12);
      } else if (cleaned.length < 12) {
        // Si es muy corto, rellenar con ceros (aunque esto es raro)
        while (cleaned.length < 12) {
          cleaned = cleaned + '0';
        }
      }
      
      formattedNumber = cleaned;
    }
    
    // Validación final
    if (formattedNumber.length !== 12 || !formattedNumber.startsWith('57')) {
      throw new Error(`No se pudo formatear el número: ${phone}. Formato esperado: 10 dígitos (ej: 3016475874) o con código de país (ej: 573016475874)`);
    }
    
    return formattedNumber;
  };

  // Función para formatear número de teléfono para mostrar (con + y espacios)
  const formatPhoneForDisplay = (phone: string): string => {
    if (phone.startsWith('57')) {
      return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`;
    }
    return phone;
  };

  // Función para validar y procesar una fila de datos
  const processRow = (row: any, rowIndex: number): ContactCreateRequest => {
    const phone = row['Número de Teléfono'] || row['Telefono'] || row['Phone'] || row['Número'] || '';
    const name = row['Nombre'] || row['Name'] || row['Contacto'] || '';
    
    if (!phone || !name) {
      throw new Error(`Fila ${rowIndex + 1}: Número de teléfono y nombre son obligatorios`);
    }
    
    if (name.length < 2) {
      throw new Error(`Fila ${rowIndex + 1}: El nombre debe tener al menos 2 caracteres`);
    }
    
    const formattedPhone = formatPhoneNumber(phone);
    
    return {
      phone_number: formattedPhone,
      name: name.trim(),
      is_active: true
    };
  };

  // Función para descargar plantilla de Excel
  const downloadTemplate = () => {
    const template = [
      {
        'Nombre': 'Juan Pérez',
        'Número de Teléfono': '3016475874'
      },
      {
        'Nombre': 'María García',
        'Número de Teléfono': '573001234568'
      },
      {
        'Nombre': 'Carlos López',
        'Número de Teléfono': '0301234567'
      }
    ];

    const ws = XLSX.utils.json_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Contactos');
    
    // Ajustar ancho de columnas
    ws['!cols'] = [
      { width: 20 }, // Nombre
      { width: 15 }  // Número de Teléfono
    ];
    
    XLSX.writeFile(wb, 'plantilla_contactos.xlsx');
  };

    // Función para procesar el archivo Excel y mostrar preview
  const processExcelFile = async (file: File) => {
    setIsImporting(true);
    setImportResult(null);
    setShowPreview(false);
    
    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      
      if (jsonData.length === 0) {
        throw new Error('El archivo está vacío');
      }
      
      const preview: ContactPreview[] = [];
      
      // Procesar cada fila para preview
      for (let i = 0; i < jsonData.length; i++) {
        try {
          const contact = processRow(jsonData[i], i);
          preview.push({
            contact,
            status: 'valid'
          });
        } catch (error: any) {
          preview.push({
            contact: { phone_number: '', name: '', is_active: true },
            status: 'error',
            error: error.message
          });
        }
      }
      
      setContactPreview(preview);
      setShowPreview(true);
      
    } catch (error: any) {
      setImportResult({
        success: 0,
        errors: [error.message],
        duplicates: [],
        total: 0
      });
    } finally {
      setIsImporting(false);
    }
  };

  // Función para confirmar la importación
  const confirmImport = async () => {
    setIsImporting(true);
    
    try {
      const validContacts = contactPreview
        .filter(p => p.status === 'valid')
        .map(p => p.contact);
      
      if (validContacts.length === 0) {
        throw new Error('No hay contactos válidos para importar');
      }
      
      const result = await contactService.createContactsBulk(validContacts);
      
      setImportResult({
        success: result.results.created,
        errors: result.results.errors,
        duplicates: result.results.duplicates || [],
        total: contactPreview.length
      });
      
      if (result.results.created > 0) {
        onImportComplete?.();
      }
      
      setShowPreview(false);
      
    } catch (error: any) {
      setImportResult({
        success: 0,
        errors: [`Error al importar contactos: ${error.message}`],
        duplicates: [],
        total: contactPreview.length
      });
    } finally {
      setIsImporting(false);
    }
  };

  // Manejadores de drag and drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
          file.type === 'application/vnd.ms-excel' ||
          file.name.endsWith('.xlsx') ||
          file.name.endsWith('.xls')) {
        processExcelFile(file);
      } else {
        alert('Por favor selecciona un archivo Excel (.xlsx o .xls)');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processExcelFile(file);
    }
  };

  const handleClose = () => {
    setImportResult(null);
    onClose?.();
  };

  return (
    <div className="modal-overlay">
      <div className="modal import-modal">
        <div className="modal-header">
          <h4>Importar Contactos</h4>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>
        
        <div className="import-content">
          {!showPreview && !importResult && (
            <>
              <div className="upload-section">
                <div className="section-header">
                  <h5>📤 Subir archivo</h5>
                  <p>Arrastra tu archivo Excel aquí o haz clic para seleccionar</p>
                </div>
                
                <div 
                  className={`upload-area ${dragActive ? 'drag-active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                  <div className="upload-icon">📁</div>
                  <p>Arrastra tu archivo Excel aquí o haz clic para seleccionar</p>
                  <span className="file-types">Formatos: .xlsx, .xls</span>
                </div>
              </div>
              
              <div className="template-section">
                                  <div className="section-header">
                    <h5>
                      <span className="material-icons">description</span>
                      Plantilla
                    </h5>
                    <p>Descarga la plantilla con el formato correcto</p>
                  </div>
                <div className="format-info">
                  <span className="format-label">Formatos soportados:</span>
                                   <div className="format-examples">
                   <span>3016475874</span>
                   <span>573001234567</span>
                   <span>0301234567</span>
                 </div>
                </div>
                <button 
                  className="download-template-btn"
                  onClick={downloadTemplate}
                  disabled={isImporting}
                >
                  Descargar Plantilla
                </button>
              </div>
            </>
          )}
          
          {isImporting && (
            <div className="importing-status">
              <div className="loading-spinner"></div>
              <p>Procesando archivo...</p>
            </div>
          )}
          
          {showPreview && (
            <div className="preview-section">
                              <div className="section-header">
                  <h5>
                    <span className="material-icons">preview</span>
                    Vista previa
                  </h5>
                  <p>Revisa los contactos antes de importar</p>
                </div>
              
              <div className="preview-list">
                {contactPreview.map((item, index) => (
                  <div key={index} className={`preview-item ${item.status}`}>
                                         <div className="preview-info">
                       <span className="contact-name">{item.contact.name}</span>
                       <span className="contact-phone">{formatPhoneForDisplay(item.contact.phone_number)}</span>
                     </div>
                    <div className="preview-status">
                      {item.status === 'valid' && <span className="status-valid">✓</span>}
                      {item.status === 'error' && <span className="status-error">✗</span>}
                      {item.status === 'duplicate' && <span className="status-duplicate">⚠</span>}
                    </div>
                    {item.error && <div className="preview-error">{item.error}</div>}
                  </div>
                ))}
              </div>
              
              <div className="preview-summary">
                <div className="summary-item">
                  <span className="summary-label">Válidos:</span>
                  <span className="summary-value valid">
                    {contactPreview.filter(p => p.status === 'valid').length}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Errores:</span>
                  <span className="summary-value error">
                    {contactPreview.filter(p => p.status === 'error').length}
                  </span>
                </div>
              </div>
              
              <div className="preview-actions">
                <button 
                  className="confirm-btn"
                  onClick={confirmImport}
                  disabled={contactPreview.filter(p => p.status === 'valid').length === 0}
                >
                  <span className="material-icons">cloud_upload</span>
                  Importar Contactos
                </button>
                <button 
                  className="cancel-btn"
                  onClick={() => setShowPreview(false)}
                >
                  <span className="material-icons">close</span>
                  Cancelar
                </button>
              </div>
            </div>
          )}
          
          {importResult && (
            <div className="import-result">
              <div className="section-header">
                <h5>📊 Resultado</h5>
                <p>Importación completada</p>
              </div>
              
              <div className="result-summary">
                <div className="result-item success">
                  <span className="result-label">Importados</span>
                  <span className="result-value">{importResult.success}</span>
                </div>
                <div className="result-item total">
                  <span className="result-label">Total</span>
                  <span className="result-value">{importResult.total}</span>
                </div>
                {importResult.duplicates.length > 0 && (
                  <div className="result-item duplicates">
                    <span className="result-label">Duplicados</span>
                    <span className="result-value">{importResult.duplicates.length}</span>
                  </div>
                )}
                {importResult.errors.length > 0 && (
                  <div className="result-item errors">
                    <span className="result-label">Errores</span>
                    <span className="result-value">{importResult.errors.length}</span>
                  </div>
                )}
              </div>
              
              {(importResult.errors.length > 0 || importResult.duplicates.length > 0) && (
                <div className="result-details">
                  {importResult.duplicates.length > 0 && (
                    <div className="detail-section">
                      <h6>Duplicados</h6>
                      <ul>
                        {importResult.duplicates.map((duplicate, index) => (
                          <li key={index}>{duplicate}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {importResult.errors.length > 0 && (
                    <div className="detail-section">
                      <h6>Errores</h6>
                      <ul>
                        {importResult.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="modal-actions">
          <button onClick={handleClose}>
            <span className="material-icons">{importResult ? 'check_circle' : 'close'}</span>
            {importResult ? 'Cerrar' : 'Cancelar'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContactImport; 