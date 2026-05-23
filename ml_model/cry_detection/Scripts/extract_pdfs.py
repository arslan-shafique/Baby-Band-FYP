import sys
try:
    from pypdf import PdfReader
except ImportError:
    try:
        import PyPDF2 as PdfReader
    except ImportError:
        print("Please install pypdf: pip install pypdf")
        sys.exit(1)

def extract_pdf_text(pdf_path, output_path):
    print(f"Extracting {pdf_path}...")
    try:
        reader = PdfReader.PdfReader(pdf_path) if hasattr(PdfReader, 'PdfReader') else PdfReader(pdf_path)
        with open(output_path, "w", encoding="utf-8") as f:
            max_pages = min(10, len(reader.pages))
            for i in range(max_pages):
                text = reader.pages[i].extract_text()
                if text:
                    f.write(f"--- PAGE {i+1} ---\n")
                    f.write(text + "\n\n")
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

pdf1 = "/home/umairimran/OLD DISK/Smart Baby Band FYP/ml_model/cry_detection/data/notes/literature/deepcraft-ready-model-for-baby-cry-detection.pdf"
pdf2 = "/home/umairimran/OLD DISK/Smart Baby Band FYP/ml_model/cry_detection/data/notes/literature/ICASSP_2022_Final.pdf"

extract_pdf_text(pdf1, "deepcraft_summary.txt")
extract_pdf_text(pdf2, "icassp2022_summary.txt")
