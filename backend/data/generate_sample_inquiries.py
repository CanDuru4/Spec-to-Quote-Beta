"""Generate 1-2 sample inquiry PDFs for evaluator demo."""
import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    print("Install reportlab: pip install reportlab")
    raise

OUTPUT_DIR = Path(__file__).resolve().parent / "sample_inquiries"
OUTPUT_DIR.mkdir(exist_ok=True)


def draw_inquiry_1(c: canvas.Canvas) -> None:
    c.setFont("Helvetica", 14)
    c.drawString(72, 720, "REQUEST FOR QUOTE - Coating Services")
    c.setFont("Helvetica", 10)
    c.drawString(72, 690, "Customer: Semiconductor Solutions Inc")
    c.drawString(72, 672, "Contact: Jane Smith, jane.smith@semisolutions.com")
    c.drawString(72, 654, "Date: March 15, 2024")
    c.drawString(72, 624, "Part description: Wafer handling chuck, aluminum substrate.")
    c.drawString(72, 606, "We need a corrosion-resistant coating for use in semiconductor process equipment.")
    c.drawString(72, 588, "Environment: Chemical exposure, cleanroom. Quantity: 12 pieces.")
    c.drawString(72, 570, "Requested turnaround: 2 weeks. Please confirm if you can meet chemical resistance")
    c.drawString(72, 552, "per our spec sheet (attached). Substrate: 6061-T6 aluminum.")
    c.drawString(72, 522, "Missing from this request: dimensions and drawing revision; cert requirements TBD.")


def draw_inquiry_2(c: canvas.Canvas) -> None:
    c.setFont("Helvetica", 14)
    c.drawString(72, 720, "COATING INQUIRY")
    c.setFont("Helvetica", 10)
    c.drawString(72, 690, "Customer: MedDevice Co")
    c.drawString(72, 672, "Part: Surgical instrument housing, stainless steel.")
    c.drawString(72, 654, "Quantity: 500. End use: Medical device, sterilization cycles.")
    c.drawString(72, 636, "We are looking for e-coat or equivalent for corrosion protection and appearance.")
    c.drawString(72, 618, "Need quote for first article and production run. Target turnaround 14 days.")
    c.drawString(72, 588, "Certification: ISO 13485 preferred. Please advise masking and packaging options.")
    c.drawString(72, 558, "Drawing and material cert attached. Substrate: 316L stainless.")


def main() -> None:
    # Sample 1: Semiconductor inquiry
    path1 = OUTPUT_DIR / "inquiry_semiconductor_wafer_chuck.pdf"
    c1 = canvas.Canvas(str(path1), pagesize=letter)
    draw_inquiry_1(c1)
    c1.save()
    print(f"Wrote {path1}")

    # Sample 2: Medical device inquiry
    path2 = OUTPUT_DIR / "inquiry_medical_housing.pdf"
    c2 = canvas.Canvas(str(path2), pagesize=letter)
    draw_inquiry_2(c2)
    c2.save()
    print(f"Wrote {path2}")


if __name__ == "__main__":
    main()
