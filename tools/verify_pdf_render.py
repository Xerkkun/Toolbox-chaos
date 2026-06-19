import os
import sys
import argparse
from PyQt6.QtCore import QSize, QPoint
from PyQt6.QtGui import QImage, QPainter, QColor
from PyQt6.QtPdf import QPdfDocument
import pypdf
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(description="Verificador parametrizado de renderizado de PDF.")
    parser.add_argument("--pdf", required=True, help="Ruta del archivo PDF a verificar.")
    parser.add_argument("--profile", required=True, choices=["dictionary", "sprott", "wang2021"], help="Perfil de validación.")
    return parser.parse_args()

def analyze_pdf(pdf_path, profile):
    # Verify input exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
        
    log_path = os.path.splitext(pdf_path)[0] + ".log"
    output_dir = f"reports/rendered_pages/{profile}"
    report_path = f"reports/pdf_render_check_{profile}.md"
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    print(f"Opening PDF: {pdf_path} under profile: {profile}")
    doc = QPdfDocument(None)
    doc.load(pdf_path)
    if doc.status() != QPdfDocument.Status.Ready:
        print("Error: Failed to load PDF!")
        sys.exit(1)
        
    num_pages = doc.pageCount()
    print(f"Total pages: {num_pages}")
    
    if num_pages == 0:
        print("Error: PDF has 0 pages!")
        sys.exit(1)
        
    # Text verification using pypdf
    reader = pypdf.PdfReader(pdf_path)
    all_text = ""
    for idx, page in enumerate(reader.pages):
        all_text += f"\n--- Page {idx+1} ---\n" + (page.extract_text() or "")
        
    # Profile constraints
    required_keywords = []
    forbidden_keywords = []
    
    if profile == "dictionary":
        required_keywords = [
            "Diccionario, manual y referencia",
            "Sistemas implementados",
            "Lorenz",
            "Rossler",
            "FFT",
            "Lyapunov",
            "Unified Lorenz",
            "Sprott S"
        ]
        forbidden_keywords = [
            "del libro de Wang"
        ]
    elif profile == "sprott":
        required_keywords = [
            "del Explorador Sprott",
            "compacta",
            "Familias especiales",
            "Reproducibilidad y atribu"
        ]
        forbidden_keywords = [
            "del libro de Wang",
            "Kuznetsov y Chen",
            "Lorenz system",
            "Rossler system",
            "Chua circuit",
            "wang_systems"
        ]
    elif profile == "wang2021":
        required_keywords = [
            "Catálogo de sistemas del libro de Wang, Kuznetsov y Chen",
            "Lorenz",
            "Rössler",
            "Chua",
            "Sprott A"
        ]
        forbidden_keywords = []
        
    # Check assertions
    failed_assertions = []
    for kw in required_keywords:
        if kw.lower() not in all_text.lower():
            failed_assertions.append(f"Falta palabra clave obligatoria: '{kw}'")
            
    for kw in forbidden_keywords:
        if kw.lower() in all_text.lower():
            failed_assertions.append(f"Contiene palabra clave prohibida: '{kw}'")
            
    # Render pages and check for blank pages
    page_stats = []
    for page_idx in range(num_pages):
        width, height = 1240, 1754 # A4 at 150 DPI
        
        # White background canvas
        canvas = QImage(width, height, QImage.Format.Format_ARGB32)
        canvas.fill(QColor(255, 255, 255))
        
        img = doc.render(page_idx, QSize(width, height))
        
        # Draw PDF page on top of white canvas
        painter = QPainter(canvas)
        painter.drawImage(QPoint(0, 0), img)
        painter.end()
        
        png_filename = f"page_{page_idx+1:03d}.png"
        png_path = os.path.join(output_dir, png_filename)
        canvas.save(png_path)
        
        # Analyze pixel data to check for blank pages
        ptr = canvas.bits()
        ptr.setsize(canvas.height() * canvas.width() * 4)
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((canvas.height(), canvas.width(), 4))
        
        # Calculate background proportion
        rgb = arr[:, :, :3]
        is_white = np.all(rgb == 255, axis=-1)
        white_ratio = float(np.mean(is_white))
        
        is_blank = white_ratio > 0.999
        page_stats.append({
            "page": page_idx + 1,
            "white_ratio": white_ratio,
            "is_blank": is_blank,
            "image_path": png_path
        })
        
        if is_blank:
            failed_assertions.append(f"Página {page_idx+1} está vacía (blanca).")
            
    # Analyze LaTeX log if exists
    log_summary = {
        "errors": [],
        "warnings": [],
        "overfull_hboxes": 0,
        "underfull_hboxes": 0
    }
    
    if os.path.exists(log_path):
        with open(log_path, "r", errors="ignore") as f:
            log_lines = f.readlines()
        for line in log_lines:
            if line.startswith("!"):
                log_summary["errors"].append(line.strip())
            elif "Warning:" in line:
                log_summary["warnings"].append(line.strip())
            elif "Overfull \\hbox" in line:
                log_summary["overfull_hboxes"] += 1
            elif "Underfull \\hbox" in line:
                log_summary["underfull_hboxes"] += 1
                
    rel_pdf_path = os.path.relpath(pdf_path, start=os.getcwd()).replace('\\', '/')
    # Build Markdown report using relative paths
    report_md = f"""# Reporte de Validación: Perfil `{profile}`

- **PDF verificado**: `{rel_pdf_path}`
- **Número de páginas**: {num_pages}
- **Estado de validación**: {"❌ FALLIDO" if failed_assertions else "✅ EXITOSO"}

## Aserciones de Contenido y Renderizado
"""
    if failed_assertions:
        report_md += "### Errores de Aserción Detectados:\n"
        for fa in failed_assertions:
            report_md += f"- ❌ {fa}\n"
    else:
        report_md += "- ✅ Todas las palabras clave requeridas están presentes.\n"
        report_md += "- ✅ Ninguna palabra clave prohibida está presente.\n"
        report_md += "- ✅ Ninguna página está vacía.\n"
        
    report_md += """
---

## Cobertura de Palabras Clave
| Palabra clave | Tipo | Encontrada |
|---|:---:|:---:|
"""
    for kw in required_keywords:
        found = "✅ SÍ" if kw.lower() in all_text.lower() else "❌ NO"
        report_md += f"| {kw} | Requerida | {found} |\n"
    for kw in forbidden_keywords:
        found = "❌ SÍ (Error)" if kw.lower() in all_text.lower() else "✅ NO"
        report_md += f"| {kw} | Prohibida | {found} |\n"
        
    report_md += """
---

## Páginas Renderizadas
Se convirtieron todas las páginas a imágenes PNG de alta resolución. A continuación se reporta la proporción de píxeles de fondo blanco:

| Página | Proporción Fondo Blanco | ¿Está Vacía? | Captura de Pantalla |
|---|---|:---:|---|
"""
    for stat in page_stats:
        status_blank = "⚠️ VACÍA" if stat['is_blank'] else "✅ OK"
        # Relative path from the report file to the image file
        rel_img_path = os.path.relpath(stat['image_path'], start=os.path.dirname(report_path)).replace("\\", "/")
        report_md += f"| Page {stat['page']} | {stat['white_ratio']*100:.2f}% | {status_blank} | [{os.path.basename(stat['image_path'])}]({rel_img_path}?width=300) |\n"
        
    report_md += f"""
---

## Diagnóstico del Log LaTeX
- **Errores**: {len(log_summary['errors'])}
- **Advertencias**: {len(log_summary['warnings'])}
- **Cajas desbordadas (Overfull \\hbox)**: {log_summary['overfull_hboxes']}
- **Cajas con bajo contenido (Underfull \\hbox)**: {log_summary['underfull_hboxes']}
"""
    if log_summary['errors']:
        report_md += "\n### Detalle de Errores:\n```\n" + "\n".join(log_summary['errors']) + "\n```\n"
        
    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"Report written to: {report_path}")
    
    if failed_assertions:
        print("Validation FAILED with errors:")
        for fa in failed_assertions:
            print(f"  - {fa}")
        sys.exit(1)
    else:
        print("Validation SUCCESSFUL!")

def main():
    args = parse_args()
    analyze_pdf(args.pdf, args.profile)

if __name__ == "__main__":
    main()
