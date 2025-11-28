"""
Uploaded File and Processing Result Models
"""
from datetime import datetime
from . import db


class UploadedFile(db.Model):
    """
    Representa un archivo Excel subido por el usuario.
    Relación 1:N con ProcessingResult (múltiples versiones).
    """
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    document_number = db.Column(db.String(50))  # [DEPRECATED] Auto-rellenado para compatibilidad
    processing_status = db.Column(db.String(20), default='processing')
    status_details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación 1:N con resultados (múltiples versiones)
    results = db.relationship('ProcessingResult', backref='uploaded_file', 
                             cascade='all, delete-orphan', 
                             order_by='ProcessingResult.version_number.desc()')
    
    def to_dict(self, include_results=False):
        """
        Serializa el archivo a diccionario.
        
        Args:
            include_results: Si True, incluye array de versiones completo
        """
        # Obtener perfil del resultado más reciente
        latest_perfil = self.results[0].perfil_usado if self.results else None
        
        data = {
            'id': self.id,
            'file_path': self.file_path,
            'filename': self.file_name,  # ← Para compatibilidad con frontend
            'file_name': self.file_name,  # ← IDENTIFICADOR PRINCIPAL
            'file_extension': self.file_extension,
            'document_number': self.document_number,  # ← DEPRECATED (compatibilidad)
            'status': self.processing_status,  # ← Para compatibilidad con frontend
            'processing_status': self.processing_status,
            'status_details': self.status_details,
            'perfil': latest_perfil,  # ← Perfil del último procesamiento
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_versions': len(self.results) if self.results else 0,
            'latest_version': self.results[0].version_number if self.results else None
        }
        
        if include_results and self.results:
            data['processing_results'] = [result.to_dict(include_data=False) for result in self.results]
        
        return data


class ProcessingResult(db.Model):
    """
    Representa el resultado de un procesamiento (versión específica).
    Múltiples versiones pueden existir para un mismo archivo.
    """
    __tablename__ = 'processing_results'
    
    id = db.Column(db.Integer, primary_key=True)
    uploaded_file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    
    # Versionamiento
    version_number = db.Column(db.Integer, nullable=False, default=1)
    
    # UUID para directorio de almacenamiento (UUIDv4)
    storage_uuid = db.Column(db.String(36), nullable=False, unique=True)
    
    # Resultados como JSONB
    resultados = db.Column(db.JSON, nullable=False)
    metricas = db.Column(db.JSON, nullable=False)
    cartilla = db.Column(db.JSON, nullable=False)
    
    # Paths de artefactos (relativos a upload_path)
    # Formato: filestore/{storage_uuid}/archivo.ext
    graph_image_path = db.Column(db.String(500))
    pdf_path = db.Column(db.String(500))
    excel_path = db.Column(db.String(500))  # Copia del Excel original
    
    # Estado del resultado
    result_status = db.Column(db.String(20), default='processing')
    # Estados: 'completed', 'error_generation', 'processing'
    error_message = db.Column(db.Text)
    
    # Metadata
    perfil_usado = db.Column(db.String(20))
    processing_time_seconds = db.Column(db.Numeric(10, 2))
    pdf_template_version = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_data=False):
        """
        Serializa el resultado a diccionario.
        
        Args:
            include_data: Si True, incluye resultados/metricas/cartilla (puede ser pesado)
        """
        base_dict = {
            'id': self.id,
            'uploaded_file_id': self.uploaded_file_id,
            'version_number': self.version_number,
            'storage_uuid': self.storage_uuid,
            'graph_image_path': self.graph_image_path,
            'pdf_path': self.pdf_path,
            'excel_path': self.excel_path,
            'status': self.result_status,  # ← Para compatibilidad con frontend
            'result_status': self.result_status,
            'error_message': self.error_message,
            'perfil_usado': self.perfil_usado,
            'processing_time_seconds': float(self.processing_time_seconds) if self.processing_time_seconds else None,
            'pdf_template_version': self.pdf_template_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'has_pdf': self.pdf_path is not None,
            'has_graph': self.graph_image_path is not None,
            'has_excel': self.excel_path is not None
        }
        
        if include_data:
            base_dict.update({
                'resultados': self.resultados,
                'metricas': self.metricas,
                'cartilla': self.cartilla
            })
        
        return base_dict
