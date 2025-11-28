"""
Flask API para ejecutar OICA - Optimizador Inteligente de Cortes de Acero
Servidor que proporciona endpoints para procesar cartillas de acero
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
import threading
import time
import os
from datetime import datetime

# Importar la función main del módulo principal
try:
    from main import main, cargar_cartilla_acero, cargar_barras_estandar
except ImportError as e:
    print(f"Error importando módulos principales: {e}")
    main = None

# Configuración de la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables globales para el estado del procesamiento
procesamiento_activo = False
ultimo_resultado = None
historial_procesamiento = []

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado del servidor
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "OICA - Optimizador Inteligente de Cortes de Acero",
        "version": "1.0.0"
    }), 200

@app.route('/status', methods=['GET'])
def get_status():
    """
    Endpoint para obtener el estado actual del procesamiento
    """
    return jsonify({
        "procesamiento_activo": procesamiento_activo,
        "ultimo_resultado": ultimo_resultado,
        "historial_procesamiento": len(historial_procesamiento),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/start-oica', methods=['POST'])
def start_oica():
    """
    Endpoint principal para iniciar el proceso de optimización OICA
    
    Acepta parámetros de configuración opcionalmente:
    - perfil_algoritmo: 'rapido', 'balanceado', 'intensivo'
    - archivo_cartilla: ruta personalizada del archivo de cartilla
    - archivo_barras: ruta personalizada del archivo de barras estándar
    - parametros_algoritmo: configuraciones específicas del AG
    """
    global procesamiento_activo, ultimo_resultado
    
    try:
        # Verificar si ya hay un procesamiento en curso
        # if procesamiento_activo:
        #     return jsonify({
        #         "error": "Ya hay un procesamiento en curso",
        #         "message": "Espere a que termine el procesamiento actual",
        #         "status": "busy"
        #     }), 409
        
        # Verificar que la función main esté disponible
        if main is None:
            return jsonify({
                "error": "Función main no disponible",
                "message": "Error en la importación de módulos principales",
                "status": "error"
            }), 500
        
        # Obtener parámetros de la solicitud (opcional)
        data = request.get_json() if request.is_json else {}
        
        perfil_algoritmo = data.get('perfil_algoritmo', 'intensivo')
        archivo_cartilla = data.get('archivo_cartilla', 'cartilla_acero.csv')
        archivo_barras = data.get('archivo_barras', 'barras_estandar.json')
        parametros_personalizados = data.get('parametros_algoritmo', {})
        
        logger.info(f"Iniciando procesamiento OICA con perfil: {perfil_algoritmo}")
        
        # Verificar que los archivos existan
        if not os.path.exists(archivo_cartilla):
            return jsonify({
                "error": "Archivo de cartilla no encontrado",
                "message": f"No se encontró el archivo: {archivo_cartilla}",
                "status": "error"
            }), 400
        
        if not os.path.exists(archivo_barras):
            return jsonify({
                "error": "Archivo de barras estándar no encontrado", 
                "message": f"No se encontró el archivo: {archivo_barras}",
                "status": "error"
            }), 400
        
        # Marcar como procesamiento activo
        procesamiento_activo = True
        
        # Registro del inicio del procesamiento
        registro_procesamiento = {
            "id": len(historial_procesamiento) + 1,
            "inicio": datetime.now().isoformat(),
            "fin": None,
            "duracion": None,
            "perfil": perfil_algoritmo,
            "archivo_cartilla": archivo_cartilla,
            "archivo_barras": archivo_barras,
            "estado": "procesando",
            "resultado": None,
            "error": None
        }
        
        historial_procesamiento.append(registro_procesamiento)
        
        def ejecutar_procesamiento():
            """
            Función para ejecutar el procesamiento en un hilo separado
            """
            global procesamiento_activo, ultimo_resultado
            
            inicio_tiempo = time.time()
            
            try:
                logger.info("Ejecutando función main() de OICA...")
                
                # Ejecutar la función main
                main()
                
                fin_tiempo = time.time()
                duracion = fin_tiempo - inicio_tiempo
                
                # Actualizar registro
                registro_procesamiento["fin"] = datetime.now().isoformat()
                registro_procesamiento["duracion"] = round(duracion, 2)
                registro_procesamiento["estado"] = "completado"
                
                # Intentar leer los archivos de resultados generados
                resultado_files = {}
                
                if os.path.exists('resultados_optimizacion_cortes.csv'):
                    resultado_files["resultados_csv"] = "resultados_optimizacion_cortes.csv"
                    
                if os.path.exists('PLAN_DE_CORTE_EJECUTABLE_AUTO.md'):
                    resultado_files["plan_ejecutable"] = "PLAN_DE_CORTE_EJECUTABLE_AUTO.md"
                
                resultado = {
                    "status": "success",
                    "message": "Procesamiento OICA completado exitosamente",
                    "duracion_segundos": round(duracion, 2),
                    "perfil_usado": perfil_algoritmo,
                    "archivos_generados": resultado_files,
                    "timestamp": datetime.now().isoformat()
                }
                
                registro_procesamiento["resultado"] = resultado
                ultimo_resultado = resultado
                
                logger.info(f"Procesamiento completado en {duracion:.2f} segundos")
                
            except Exception as e:
                fin_tiempo = time.time()
                duracion = fin_tiempo - inicio_tiempo
                
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                logger.error(f"Error en el procesamiento: {error_msg}")
                logger.error(f"Trace completo: {error_trace}")
                
                # Actualizar registro con error
                registro_procesamiento["fin"] = datetime.now().isoformat()
                registro_procesamiento["duracion"] = round(duracion, 2)
                registro_procesamiento["estado"] = "error"
                registro_procesamiento["error"] = error_msg
                
                ultimo_resultado = {
                    "status": "error",
                    "message": f"Error durante el procesamiento: {error_msg}",
                    "duracion_segundos": round(duracion, 2),
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                procesamiento_activo = False
        
        # Iniciar el procesamiento en un hilo separado
        thread = threading.Thread(target=ejecutar_procesamiento)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Procesamiento OICA iniciado exitosamente",
            "procesamiento_id": registro_procesamiento["id"],
            "perfil_algoritmo": perfil_algoritmo,
            "timestamp": datetime.now().isoformat(),
            "info": "Use el endpoint /status para monitorear el progreso"
        }), 202
        
    except Exception as e:
        procesamiento_activo = False
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        logger.error(f"Error iniciando procesamiento: {error_msg}")
        logger.error(f"Trace: {error_trace}")
        
        return jsonify({
            "error": "Error interno del servidor",
            "message": error_msg,
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/historial', methods=['GET'])
def get_historial():
    """
    Endpoint para obtener el historial de procesamientos
    """
    return jsonify({
        "historial": historial_procesamiento,
        "total_procesamientos": len(historial_procesamiento),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/resultados/<path:filename>', methods=['GET'])
def get_resultados(filename):
    """
    Endpoint para descargar archivos de resultados generados
    """
    try:
        if not os.path.exists(filename):
            return jsonify({
                "error": "Archivo no encontrado",
                "message": f"El archivo {filename} no existe",
                "status": "not_found"
            }), 404
        
        # Para archivos CSV, devolver como JSON
        if filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(filename)
            return jsonify({
                "filename": filename,
                "data": df.to_dict('records'),
                "total_records": len(df),
                "timestamp": datetime.now().isoformat()
            })
        
        # Para archivos de texto/markdown, devolver contenido
        elif filename.endswith(('.md', '.txt')):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                "filename": filename,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            return jsonify({
                "error": "Tipo de archivo no soportado",
                "message": "Solo se soportan archivos .csv, .md y .txt",
                "status": "unsupported"
            }), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {str(e)}")
        return jsonify({
            "error": "Error leyendo archivo",
            "message": str(e),
            "status": "error"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Manejo de rutas no encontradas"""
    return jsonify({
        "error": "Endpoint no encontrado",
        "message": "La ruta solicitada no existe",
        "status": "not_found",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejo de errores internos del servidor"""
    return jsonify({
        "error": "Error interno del servidor",
        "message": "Ocurrió un error inesperado en el servidor",
        "status": "internal_error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    # Configuración del servidor
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info("Iniciando servidor OICA Flask API...")
    logger.info(f"Puerto: {port}")
    logger.info(f"Debug: {debug}")
    
    # Verificar archivos necesarios al inicio
    if not os.path.exists('cartilla_acero.csv'):
        logger.warning("Archivo cartilla_acero.csv no encontrado")
    if not os.path.exists('barras_estandar.json'):
        logger.warning("Archivo barras_estandar.json no encontrado")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
