"""
Módulo para generación de artefactos de optimización:
- Excel con resultados detallados
- PDF con plan de corte formateado
- Imagen PNG con gráfica de barras

Todos los artefactos se guardan en directorios UUID aislados.
"""
import os
import json
import tempfile
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from weasyprint import HTML
from typing import Dict, Tuple


def generar_artefactos_completos(
    resultados_df: pd.DataFrame,
    storage_uuid: str,
    filestore_base: str = 'data/filestore',
    document_number: str = ''
) -> Tuple[str, str, str]:
    """
    Genera los 3 artefactos de optimización en un directorio UUID.
    
    Args:
        resultados_df: DataFrame con columnas optimizadas
        storage_uuid: UUID para directorio de almacenamiento
        filestore_base: Ruta base del filestore
        document_number: Número de documento para metadatos
        
    Returns:
        Tuple de (excel_path, pdf_path, image_path)
        
    Raises:
        ValueError: Si resultados_df está vacío o faltan columnas
        IOError: Si hay errores al escribir archivos
    """
    # Validar entrada
    if resultados_df.empty:
        raise ValueError("resultados_df está vacío")
    
    required_cols = [
        'numero_barra', 'barra_origen_longitud', 'cortes_realizados',
        'cantidad_requerida', 'masa_unitaria_kg', 'desperdicio_m'
    ]
    missing = [col for col in required_cols if col not in resultados_df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    
    # Crear directorio UUID
    storage_dir = os.path.join(filestore_base, storage_uuid)
    os.makedirs(storage_dir, exist_ok=True)
    
    # 1. Generar Excel
    excel_path = os.path.join(storage_dir, 'resultados_optimizacion.xlsx')
    resultados_df.to_excel(excel_path, index=False)
    
    # 2. Generar PDF
    pdf_path = generar_pdf_con_link_correcto(
        resultados_df,
        storage_dir,
        document_number
    )
    
    # 3. Generar imagen
    image_path = generar_imagen_grafica(
        resultados_df,
        storage_dir
    )
    
    return excel_path, pdf_path, image_path


def generar_pdf_con_link_correcto(
    resultados_df: pd.DataFrame,
    storage_dir: str,
    document_number: str = ''
) -> str:
    """
    Genera un PDF con el plan de corte formateado usando plantilla HTML.
    
    Args:
        resultados_df: DataFrame con resultados de optimización
        storage_dir: Directorio donde guardar el PDF
        document_number: Número de documento para el título
        
    Returns:
        Ruta al archivo PDF generado
    """
    pdf_path = os.path.join(storage_dir, 'plan_de_corte.pdf')
    
    # Calcular métricas
    total_barras = len(resultados_df)
    total_masa = resultados_df['masa_unitaria_kg'].sum()
    total_desperdicio = resultados_df['desperdicio_m'].sum()
    eficiencia = ((total_masa - total_desperdicio) / total_masa * 100) if total_masa > 0 else 0
    
    # Generar tabla HTML
    tabla_html = "<table>"
    tabla_html += """
    <tr>
        <th>Barra</th>
        <th>Longitud</th>
        <th>Cortes</th>
        <th>Cantidad</th>
        <th>Desperdicio</th>
    </tr>
    """
    
    for _, row in resultados_df.iterrows():
        cortes_str = ", ".join([f"{c:.2f}m" for c in row['cortes_realizados']])
        tabla_html += f"""
        <tr>
            <td>{row['numero_barra']}</td>
            <td>{row['barra_origen_longitud']:.2f}m</td>
            <td>{cortes_str}</td>
            <td>{row['cantidad_requerida']}</td>
            <td>{row['desperdicio_m']:.3f}m</td>
        </tr>
        """
    
    tabla_html += "</table>"
    
    # Plantilla HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
            }}
            .metrics {{
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .metrics p {{
                margin: 8px 0;
                font-size: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #bdc3c7;
                font-size: 12px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <h1>Plan de Corte Optimizado</h1>
        <p><strong>Documento:</strong> {document_number or 'N/A'}</p>
        
        <div class="metrics">
            <h2>Resumen Ejecutivo</h2>
            <p><strong>Total de barras:</strong> {total_barras}</p>
            <p><strong>Masa total:</strong> {total_masa:.2f} kg</p>
            <p><strong>Desperdicio total:</strong> {total_desperdicio:.3f} m</p>
            <p><strong>Eficiencia:</strong> {eficiencia:.2f}%</p>
        </div>
        
        <h2>Detalle de Cortes</h2>
        {tabla_html}
        
        <div class="footer">
            <p>Este plan fue generado automáticamente usando algoritmos genéticos para maximizar 
            la eficiencia del material y minimizar desperdicios. Los patrones han sido optimizados 
            considerando las longitudes comerciales disponibles y las cantidades requeridas específicas 
            del proyecto.</p>
        </div>
    </body>
    </html>
    """
    
    # Generar PDF con WeasyPrint
    HTML(string=html_content).write_pdf(pdf_path)
    
    return pdf_path


def generar_imagen_grafica(
    resultados_df: pd.DataFrame,
    storage_dir: str,
    max_cantidad_grafica: int = 100
) -> str:
    """
    Genera una imagen PNG con gráfica horizontal de cortes por barra.
    
    No genera gráfica si alguna orden supera max_cantidad_grafica piezas
    (evita gráficas excesivamente largas).
    
    Args:
        resultados_df: DataFrame con resultados de optimización
        storage_dir: Directorio donde guardar la imagen
        max_cantidad_grafica: Cantidad máxima para generar gráfica
        
    Returns:
        Ruta al archivo PNG generado (o None si se omite por cantidad)
        
    Raises:
        ValueError: Si cantidad excede límite
    """
    image_path = os.path.join(storage_dir, 'grafica_cortes.png')
    
    # Validar cantidades
    if 'cantidad_requerida' in resultados_df.columns:
        cantidades_numericas = pd.to_numeric(
            resultados_df['cantidad_requerida'],
            errors='coerce'
        )
        if (cantidades_numericas > max_cantidad_grafica).any():
            raise ValueError(
                f"No se puede generar gráfica: alguna orden supera {max_cantidad_grafica} piezas"
            )
    
    # Preparar datos
    barras = []
    for _, row in resultados_df.iterrows():
        diam = row['numero_barra']
        barra_len = row['barra_origen_longitud']
        cortes = row['cortes_realizados']
        barras.append((diam, barra_len, cortes))
    
    # Crear gráfica
    fig, ax = plt.subplots(figsize=(16, max(7, len(barras) * 0.5)))
    
    colors = ['#4F81BD', '#C0504D', '#9BBB59', '#8064A2', '#F79646', '#2C4D75', '#E46C0A', '#948A54']
    
    y_pos = 0
    for idx, (diam, barra_len, cortes) in enumerate(barras):
        x = 0
        # Dibujar cada corte
        for corte in cortes:
            ax.barh(
                y_pos,
                corte,
                left=x,
                color=colors[idx % len(colors)],
                edgecolor='black',
                height=0.8
            )
            x += corte
        
        # Dibujar desperdicio
        if x < barra_len:
            ax.barh(
                y_pos,
                barra_len - x,
                left=x,
                color='gray',
                alpha=0.3,
                edgecolor='black',
                height=0.8,
                hatch='//'
            )
        
        # Etiqueta
        ax.text(
            barra_len + 0.1,
            y_pos,
            f'{diam} - {barra_len:.2f}m',
            va='center',
            fontsize=8
        )
        
        y_pos += 1
    
    ax.set_xlabel('Longitud (m)', fontsize=12)
    ax.set_ylabel('Barra', fontsize=12)
    ax.set_title('Visualización de cortes por barra', fontsize=14, fontweight='bold')
    ax.set_yticks([])
    
    plt.tight_layout()
    
    # Guardar imagen
    plt.savefig(
        image_path,
        format='png',
        bbox_inches='tight',
        dpi=200
    )
    plt.close(fig)
    
    return image_path
