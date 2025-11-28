"""
Servidor Flask principal con Socket.IO para procesamiento asíncrono.

Endpoints:
- POST /upload: Carga archivo y encola procesamiento
- GET /files: Lista archivos con filtros opcionales
- GET /file/<id>: Detalle de un archivo
- DELETE /file/<id>: Elimina archivo y versiones
- POST /reprocess/<id>: Reprocesa archivo con nuevo perfil
- GET /descargar-excel/<uuid>: Descarga Excel
- GET /descargar-pdf/<uuid>: Descarga PDF
- GET /descargar-imagen/<uuid>: Descarga imagen PNG

WebSocket:
- subscribe_task: Cliente se suscribe a actualizaciones de tarea
- task_update: Servidor emite progreso en tiempo real
"""
import os
import json
import redis
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import pandas as pd

from models import db, UploadedFile, ProcessingResult
from celery_worker import celery_app, process_file_task


# ============================================================================
# CONFIGURACIÓN DE FLASK Y EXTENSIONES
# ============================================================================

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://oica_user:oica_password@db:5432/oica_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# Inicializar extensiones
db.init_app(app)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    logger=True,
    engineio_logger=True
)

# Directorio para filestore
FILESTORE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'filestore')
os.makedirs(FILESTORE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

# Cliente Redis para Pub/Sub
redis_client = redis.Redis.from_url(
    os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    decode_responses=True
)


# ============================================================================
# UTILIDADES
# ============================================================================

def allowed_file(filename):
    """Valida extensión de archivo."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_perfil(perfil):
    """Valida que el perfil sea uno de los permitidos."""
    perfiles_validos = ['rapido', 'balanceado', 'profundo']
    return perfil in perfiles_validos


# ============================================================================
# ENDPOINTS HTTP
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para Docker."""
    try:
        # Verificar conexión a BD
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para cargar archivo y encolar procesamiento asíncrono.
    
    Form data:
        - file: Archivo XLSX o CSV
        - documentNumber: Número de documento (opcional)
        - perfil: rapido | balanceado | profundo (default: balanceado)
    
    Returns:
        {
            "file_id": int,
            "task_id": str,
            "status": "uploaded",
            "message": "Archivo encolado para procesamiento"
        }
    """
    # Validar archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Extensión no permitida',
            'allowed': list(ALLOWED_EXTENSIONS)
        }), 400
    
    # Validar perfil
    perfil = request.form.get('perfil', 'balanceado')
    if not validate_perfil(perfil):
        return jsonify({
            'error': 'Perfil inválido',
            'allowed': ['rapido', 'balanceado', 'profundo']
        }), 400
    
    # Obtener metadata del archivo
    filename = secure_filename(file.filename)
    # Auto-rellenar document_number desde filename (sin extensión) para compatibilidad
    document_number = os.path.splitext(filename)[0]
    
    try:
        # Guardar archivo temporalmente para Celery
        temp_dir = os.path.join(FILESTORE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{datetime.now().timestamp()}_{filename}")
        file.save(temp_path)
        
        # Crear registro en BD
        uploaded_file = UploadedFile(
            file_name=filename,
            file_path=temp_path,
            file_extension=os.path.splitext(filename)[1][1:],  # Sin el punto
            document_number=document_number
        )
        db.session.add(uploaded_file)
        db.session.commit()
        
        # Encolar tarea en Celery
        task = process_file_task.apply_async(
            args=[uploaded_file.id, perfil],
            task_id=f"process_{uploaded_file.id}"
        )
        
        return jsonify({
            'file_id': uploaded_file.id,
            'task_id': task.id,
            'status': 'uploaded',
            'message': 'Archivo encolado para procesamiento'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Error al procesar archivo',
            'details': str(e)
        }), 500


@app.route('/files', methods=['GET'])
def list_files():
    """
    Lista archivos con filtros opcionales.
    
    Query params:
        - search: Buscar en filename o document_number
        - status: Filtrar por estado
        - perfil: Filtrar por perfil
        - date_from: Fecha desde (ISO format)
        - date_to: Fecha hasta (ISO format)
        - page: Número de página (default: 1)
        - per_page: Resultados por página (default: 20)
    
    Returns:
        {
            "files": [{"id", "filename", "status", ...}],
            "total": int,
            "page": int,
            "per_page": int
        }
    """
    query = UploadedFile.query
    
    # Filtro de búsqueda (solo por nombre de archivo)
    search = request.args.get('search', '').strip()
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(UploadedFile.filename.ilike(search_pattern))
    
    # Filtro por estado
    status = request.args.get('status')
    if status:
        query = query.filter(UploadedFile.status == status)
    
    # Filtro por perfil
    perfil = request.args.get('perfil')
    if perfil:
        query = query.filter(UploadedFile.perfil == perfil)
    
    # Filtro por fechas
    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(UploadedFile.created_at >= date_from)
    
    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(UploadedFile.created_at <= date_to)
    
    # Paginación
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Ordenar por fecha descendente
    query = query.order_by(UploadedFile.created_at.desc())
    
    # Ejecutar query paginada
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Enriquecer con progreso actual de Redis para archivos en procesamiento
    files_data = []
    for f in paginated.items:
        file_dict = f.to_dict(include_results=True)
        
        # Si está en procesamiento, obtener progreso actual de Redis
        if f.processing_status in ['validating', 'processing', 'generating_artifacts']:
            task_id = f'process_{f.id}'
            try:
                progress_data = redis_client.get(f'task_progress:{task_id}')
                if progress_data:
                    import json
                    progress_info = json.loads(progress_data)
                    file_dict['current_progress'] = progress_info.get('progress', 0)
                    file_dict['current_state'] = progress_info.get('state', '')
                    file_dict['current_message'] = progress_info.get('message', '')
                else:
                    file_dict['current_progress'] = 0
            except Exception as e:
                print(f"[ERROR] No se pudo obtener progreso para {task_id}: {e}")
                file_dict['current_progress'] = 0
        else:
            file_dict['current_progress'] = 0 if f.processing_status != 'completed' else 100
        
        files_data.append(file_dict)
    
    return jsonify({
        'files': files_data,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })


@app.route('/file/<int:file_id>', methods=['GET'])
def get_file_detail(file_id):
    """
    Obtiene detalle de un archivo con todas sus versiones.
    
    Returns:
        {
            "id", "filename", "status", ...,
            "results": [{"version_number", "storage_uuid", ...}]
        }
    """
    uploaded_file = UploadedFile.query.get_or_404(file_id)
    return jsonify(uploaded_file.to_dict(include_results=True))


@app.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    Elimina archivo y todas sus versiones asociadas.
    Borra directorios UUID del filestore.
    """
    uploaded_file = UploadedFile.query.get_or_404(file_id)
    
    try:
        # Eliminar directorios de versiones
        for result in uploaded_file.processing_results:
            if result.storage_uuid:
                storage_dir = os.path.join(FILESTORE_DIR, result.storage_uuid)
                if os.path.exists(storage_dir):
                    import shutil
                    shutil.rmtree(storage_dir)
        
        # Eliminar archivo temporal original
        if uploaded_file.uploaded_file_path and os.path.exists(uploaded_file.uploaded_file_path):
            os.remove(uploaded_file.uploaded_file_path)
        
        # Eliminar registros de BD (CASCADE eliminará processing_results)
        db.session.delete(uploaded_file)
        db.session.commit()
        
        return jsonify({
            'message': 'Archivo eliminado exitosamente',
            'file_id': file_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Error al eliminar archivo',
            'details': str(e)
        }), 500


@app.route('/reprocess/<int:file_id>', methods=['POST'])
def reprocess_file(file_id):
    """
    Reprocesa un archivo con nuevo perfil.
    Crea una nueva versión de resultados.
    
    JSON body:
        {
            "perfil": "rapido" | "balanceado" | "profundo"
        }
    
    Returns:
        {
            "task_id": str,
            "file_id": int,
            "message": "Archivo encolado para reprocesamiento"
        }
    """
    uploaded_file = UploadedFile.query.get_or_404(file_id)
    
    # Validar que el archivo original exista
    if not uploaded_file.uploaded_file_path or not os.path.exists(uploaded_file.uploaded_file_path):
        return jsonify({
            'error': 'Archivo original no encontrado',
            'details': 'El archivo ya fue eliminado del sistema'
        }), 404
    
    # Obtener nuevo perfil
    data = request.get_json()
    nuevo_perfil = data.get('perfil', uploaded_file.perfil)
    
    if not validate_perfil(nuevo_perfil):
        return jsonify({
            'error': 'Perfil inválido',
            'allowed': ['rapido', 'balanceado', 'profundo']
        }), 400
    
    try:
        # Actualizar perfil si cambió
        if nuevo_perfil != uploaded_file.perfil:
            uploaded_file.perfil = nuevo_perfil
            db.session.commit()
        
        # Encolar nueva tarea
        task = process_file_task.apply_async(
            args=[uploaded_file.id, nuevo_perfil],
            task_id=f"reprocess_{uploaded_file.id}_{datetime.now().timestamp()}"
        )
        
        return jsonify({
            'task_id': task.id,
            'file_id': file_id,
            'perfil': nuevo_perfil,
            'message': 'Archivo encolado para reprocesamiento'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Error al reprocesar archivo',
            'details': str(e)
        }), 500


@app.route('/descargar-excel/<uuid>', methods=['GET'])
def download_excel(uuid):
    """Descarga archivo Excel de resultados."""
    result = ProcessingResult.query.filter_by(storage_uuid=uuid).first_or_404()
    
    if not result.excel_path or not os.path.exists(result.excel_path):
        return jsonify({'error': 'Archivo Excel no encontrado'}), 404
    
    return send_file(
        result.excel_path,
        as_attachment=True,
        download_name=f'resultados_{uuid}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/descargar-pdf/<uuid>', methods=['GET'])
def download_pdf(uuid):
    """Descarga archivo PDF con plan de corte."""
    result = ProcessingResult.query.filter_by(storage_uuid=uuid).first_or_404()
    
    if not result.pdf_path or not os.path.exists(result.pdf_path):
        return jsonify({'error': 'Archivo PDF no encontrado'}), 404
    
    return send_file(
        result.pdf_path,
        as_attachment=True,
        download_name=f'plan_corte_{uuid}.pdf',
        mimetype='application/pdf'
    )


@app.route('/descargar-imagen/<uuid>', methods=['GET'])
def download_image(uuid):
    """Descarga imagen PNG con gráfica de cortes."""
    result = ProcessingResult.query.filter_by(storage_uuid=uuid).first_or_404()
    
    if not result.graph_image_path or not os.path.exists(result.graph_image_path):
        return jsonify({'error': 'Archivo de imagen no encontrado'}), 404
    
    return send_file(
        result.graph_image_path,
        as_attachment=True,
        download_name=f'grafica_{uuid}.png',
        mimetype='image/png'
    )


@app.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Endpoint de fallback para consultar estado de tarea desde Celery.
    Se usa cuando WebSocket falla o como polling alternativo.
    """
    try:
        # Consultar estado desde Celery backend (Redis)
        task = celery_app.AsyncResult(task_id)
        
        response = {
            'task_id': task_id,
            'state': task.state,
            'progress': 0,
            'message': '',
        }
        
        if task.state == 'PENDING':
            response['message'] = 'Tarea en cola...'
        elif task.state == 'STARTED':
            response['progress'] = 5
            response['message'] = 'Procesamiento iniciado...'
        elif task.state in ['VALIDATING', 'VALIDATED', 'PROCESSING', 'GENERATING']:
            # Obtener metadata del estado
            if task.info:
                response['progress'] = task.info.get('progress', 0)
                response['message'] = task.info.get('status', '')
                response['phase'] = task.info.get('phase', '')
        elif task.state == 'SUCCESS':
            response['progress'] = 100
            response['message'] = 'Procesamiento completado'
            response['result'] = task.result
        elif task.state == 'FAILURE':
            response['message'] = str(task.info) if task.info else 'Error en procesamiento'
            response['error'] = True
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Error consultando estado de tarea',
            'details': str(e)
        }), 500


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Cliente se conecta al WebSocket."""
    print(f"Cliente conectado: {request.sid}")
    emit('connected', {'message': 'Conectado al servidor'})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente se desconecta del WebSocket."""
    print(f"Cliente desconectado: {request.sid}")


@socketio.on('subscribe_task')
def handle_subscribe_task(data):
    """
    Cliente se suscribe a actualizaciones de una tarea.
    
    Data:
        {
            "task_id": str
        }
    """
    task_id = data.get('task_id')
    if task_id:
        join_room(task_id)
        print(f"Cliente {request.sid} suscrito a tarea {task_id}")
        emit('subscribed', {'task_id': task_id, 'message': 'Suscrito a actualizaciones'})
    else:
        emit('error', {'message': 'task_id requerido'})


def emit_task_update(task_id, data):
    """
    Función helper para emitir actualizaciones de tareas.
    Llamada desde Celery worker.
    
    Args:
        task_id: ID de la tarea Celery
        data: Diccionario con estado y progreso
    """
    socketio.emit('task_update', data, room=task_id)


def redis_pubsub_listener():
    """
    Background thread que escucha mensajes de Redis Pub/Sub
    y los reenvía como eventos WebSocket.
    """
    pubsub = redis_client.pubsub()
    pubsub.psubscribe('task_progress:*')  # Suscribirse a todos los task_progress:*
    
    print('[Redis Pub/Sub] Listener iniciado, esperando mensajes...')
    
    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            try:
                # Extraer task_id del canal (task_progress:process_123 -> process_123)
                channel = message['channel']
                task_id = channel.split(':', 1)[1]
                
                # Parsear datos JSON
                data = json.loads(message['data'])
                
                # Emitir a WebSocket room correspondiente
                with app.app_context():
                    emit_task_update(task_id, data)
                    print(f'[Redis Pub/Sub] Emitido task_update para {task_id}: {data.get("progress", 0)}%')
            except Exception as e:
                print(f'[Redis Pub/Sub] Error procesando mensaje: {e}')


# ============================================================================
# INICIALIZACIÓN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Iniciar thread de Redis Pub/Sub listener
    listener_thread = threading.Thread(target=redis_pubsub_listener, daemon=True)
    listener_thread.start()
    print('[Server] Redis Pub/Sub listener thread iniciado')
    
    # Usar socketio.run en lugar de app.run
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('FLASK_DEBUG', 'False') == 'True'
    )
