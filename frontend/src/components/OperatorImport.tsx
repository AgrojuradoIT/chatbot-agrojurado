import React, { useState, useRef } from 'react';
import * as XLSX from 'xlsx';
import { operatorService } from '../services/operatorService';
import type { OperatorCreateRequest } from '../services/operatorService';
import Loader from './Loader';
import LoadingButton from './LoadingButton';
import { useNotifications } from './NotificationContainer';

interface ImportResult {
  success: number;
  errors: string[];
  duplicates: string[];
  total: number;
}

interface OperatorPreview {
  operator: OperatorCreateRequest;
  status: 'valid' | 'duplicate' | 'error';
  error?: string;
}

interface OperatorImportProps {
  onImportComplete?: () => void;
  onClose?: () => void;
}

const OperatorImport: React.FC<OperatorImportProps> = ({ onImportComplete, onClose }) => {
  const { showNotification } = useNotifications();
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [operatorPreview, setOperatorPreview] = useState<OperatorPreview[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Función para validar cédula colombiana
  const validateCedula = (cedula: string): boolean => {
    // Remover espacios y caracteres especiales
    const cleanCedula = cedula.replace(/\D/g, '');
    
    // Verificar que tenga entre 6 y 10 dígitos
    if (cleanCedula.length < 6 || cleanCedula.length > 10) {
      return false;
    }
    
    return true;
  };

  // Función para formatear cédula
  const formatCedula = (cedula: string): string => {
    return cedula.replace(/\D/g, '');
  };

  // Función para validar y procesar una fila de datos
  const processRow = (row: any, rowIndex: number): OperatorCreateRequest => {
    const cedula = row['Cédula'] || row['Cedula'] || row['Cedula de Identidad'] || row['Documento'] || '';
  const name = row['Nombre'] || row['Name'] || row['Empleado'] || row['Nombre Completo'] || '';
    const expeditionDate = row['Fecha de Expedición'] || row['Fecha Expedicion'] || row['Expedición'] || '';
    
    if (!cedula || !name || !expeditionDate) {
      throw new Error(`Fila ${rowIndex + 1}: Cédula, nombre y fecha de expedición son obligatorios`);
    }
    
    if (name.length < 2) {
      throw new Error(`Fila ${rowIndex + 1}: El nombre debe tener al menos 2 caracteres`);
    }
    
    if (!validateCedula(cedula)) {
      throw new Error(`Fila ${rowIndex + 1}: La cédula debe tener entre 6 y 10 dígitos`);
    }
    
    // Validar formato de fecha (DD/MM/YYYY o YYYY-MM-DD)
    let formattedDate: string;
    try {
      // Intentar parsear diferentes formatos de fecha
      let dateObj: Date;
      
      // Si expeditionDate es un objeto Date de Excel
      if (expeditionDate instanceof Date) {
        dateObj = expeditionDate;
      }
      // Si es un número (serial de fecha de Excel)
      else if (typeof expeditionDate === 'number') {
        // Convertir número de Excel a fecha (Excel cuenta desde 1900-01-01)
        const excelEpoch = new Date(1899, 11, 30); // Excel epoch
        dateObj = new Date(excelEpoch.getTime() + expeditionDate * 86400000);
      }
      // Si es un string
      else if (typeof expeditionDate === 'string') {
        const dateStr = expeditionDate.trim();
        
        if (dateStr.includes('/')) {
          // Formato DD/MM/YYYY
          const [day, month, year] = dateStr.split('/');
          dateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        } else if (dateStr.includes('-')) {
          // Formato YYYY-MM-DD
          dateObj = new Date(dateStr);
        } else {
          throw new Error('Formato de fecha no reconocido');
        }
      } else {
        throw new Error('Formato de fecha no reconocido');
      }
      
      if (isNaN(dateObj.getTime())) {
        throw new Error('Fecha inválida');
      }
      
      formattedDate = dateObj.toISOString();
    } catch (error) {
      throw new Error(`Fila ${rowIndex + 1}: Fecha de expedición inválida. Use formato DD/MM/YYYY o YYYY-MM-DD`);
    }
    
    return {
      cedula: formatCedula(cedula),
      name: name.trim(),
      expedition_date: formattedDate
    };
  };

  // Función para descargar plantilla de Excel
  const downloadTemplate = () => {
    const template = [
      {
        'Cédula': '12345678',
        'Nombre': 'Juan Pérez García',
        'Fecha de Expedición': '15/03/1990'
      },
      {
        'Cédula': '87654321',
        'Nombre': 'María García López',
        'Fecha de Expedición': '2020-05-20'
      },
      {
        'Cédula': '11223344',
        'Nombre': 'Carlos López Martínez',
        'Fecha de Expedición': '10/12/1985'
      }
    ];

    const ws = XLSX.utils.json_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Empleados');
    
    // Ajustar ancho de columnas
    ws['!cols'] = [
      { width: 15 }, // Cédula
      { width: 25 }, // Nombre
      { width: 20 }  // Fecha de Expedición
    ];
    
    XLSX.writeFile(wb, 'plantilla_empleados.xlsx');
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
      
      const preview: OperatorPreview[] = [];
      
      // Procesar cada fila para preview
      for (let i = 0; i < jsonData.length; i++) {
        try {
          const operator = processRow(jsonData[i], i);
          preview.push({
            operator,
            status: 'valid'
          });
        } catch (error: any) {
          preview.push({
            operator: { cedula: '', name: '', expedition_date: '' },
            status: 'error',
            error: error.message
          });
        }
      }
      
      setOperatorPreview(preview);
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
      const validOperators = operatorPreview
        .filter(p => p.status === 'valid')
        .map(p => p.operator);
      
      if (validOperators.length === 0) {
  throw new Error('No hay empleados válidos para importar');
      }
      
      const result = await operatorService.createOperatorsBulk(validOperators);
      
      setImportResult({
        success: result.results.created,
        errors: result.results.errors,
        duplicates: result.results.duplicates || [],
        total: operatorPreview.length
      });
      
      if (result.results.created > 0) {
        onImportComplete?.();
      }
      
      setShowPreview(false);
      
    } catch (error: any) {
      setImportResult({
        success: 0,
  errors: [`Error al importar empleados: ${error.message}`],
        duplicates: [],
        total: operatorPreview.length
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
        showNotification({
          type: 'warning',
          title: 'Formato de Archivo Incorrecto',
          message: 'Por favor selecciona un archivo Excel (.xlsx o .xls)'
        });
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

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('es-ES');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal import-modal">
        <div className="modal-header">
          <h4>Importar Empleados</h4>
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
                    <span>DD/MM/YYYY</span>
                    <span>YYYY-MM-DD</span>
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
              <Loader size={20} />
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
                <p>Revisa los empleados antes de importar</p>
              </div>
              
              <div className="preview-list">
                {operatorPreview.map((item, index) => (
                  <div key={index} className={`preview-item ${item.status}`}>
                    <div className="operator-preview-info">
                      <span className="operator-name">{item.operator.name}</span>
                      <span className="operator-cedula">{item.operator.cedula}</span>
                      <span className="operator-date">{formatDate(item.operator.expedition_date)}</span>
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
                    {operatorPreview.filter(p => p.status === 'valid').length}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Errores:</span>
                  <span className="summary-value error">
                    {operatorPreview.filter(p => p.status === 'error').length}
                  </span>
                </div>
              </div>
              
              <div className="preview-actions">
                <LoadingButton
                  onClick={confirmImport}
                  disabled={operatorPreview.filter(p => p.status === 'valid').length === 0}
                  loading={isImporting}
                  className="confirm-btn"
                >
                  <span className="material-icons">cloud_upload</span>
                  Importar Empleados
                </LoadingButton>
                <button 
                  className="cancel-btn"
                  onClick={() => setShowPreview(false)}
                  disabled={isImporting}
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

export default OperatorImport;
