import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build_pdf(tex_relative_path, runs=3):
    tex_path = ROOT / tex_relative_path
    if not tex_path.exists():
        print(f"Error: LaTeX source file not found: {tex_path}")
        sys.exit(1)
        
    cwd = tex_path.parent
    filename = tex_path.name
    pdf_filename = tex_path.stem + ".pdf"
    pdf_path = cwd / pdf_filename
    
    print(f"\n==================================================")
    print(f"Building PDF for: {tex_relative_path}")
    print(f"Working directory: {cwd}")
    print(f"==================================================")
    
    # Run pdflatex multiple times to resolve cross-references and TOC
    for run in range(1, runs + 1):
        print(f"Running pdflatex (Pass {run}/{runs})...")
        cmd = ["pdflatex", "-interaction=nonstopmode", filename]
        
        # Run command
        res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check for catastrophic compilation failure
        if res.returncode != 0:
            print(f"Error during compilation pass {run}!")
            print("--- Standard Error ---")
            print(res.stderr)
            print("--- Standard Output (Tail) ---")
            lines = res.stdout.splitlines()
            print("\n".join(lines[-30:]))
            
            # Print the log file if pdflatex failed
            log_path = tex_path.with_suffix(".log")
            if log_path.exists():
                print(f"\n--- LaTeX Log File Content (Tail) ---")
                with open(log_path, "r", errors="ignore") as lf:
                    log_lines = lf.readlines()
                print("".join(log_lines[-50:]))
                
            sys.exit(1)
            
    # Verification of final file
    if not pdf_path.exists():
        print(f"Error: Compiled PDF file not found at: {pdf_path}")
        sys.exit(1)
        
    size_bytes = pdf_path.stat().st_size
    if size_bytes == 0:
        print(f"Error: Compiled PDF file is empty (0 bytes) at: {pdf_path}")
        sys.exit(1)
        
    # Check page count using pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)
        if num_pages == 0:
            print(f"Error: Compiled PDF file has 0 pages: {pdf_path}")
            sys.exit(1)
        print(f"Successfully compiled {pdf_filename} ({num_pages} pages, {size_bytes} bytes)")
    except Exception as e:
        print(f"Warning: Could not verify page count via pypdf: {e}")
        print(f"Successfully compiled {pdf_filename} ({size_bytes} bytes)")

def main():
    # Build chaos_dictionary.tex
    build_pdf("assets/chaos_dictionary.tex")
    
    # Build sprott_theory.tex
    build_pdf("assets/sprott/sprott_theory.tex")
    
    print("\n==================================================")
    print("All PDFs built successfully!")
    print("==================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
