# Insurance Advisor AI — Universal Insurance Document Extractor

A Streamlit application that extracts structured policyholder details from insurance
documents across multiple formats — digital PDFs, scanned PDFs, images, CSV, Excel,
and JSON — using a combination of text parsing, OCR, and a local vision-language model.

---

## Features

- **Universal format support** — PDF (digital & scanned), JPG/PNG, CSV, XLSX, JSON
- **Smart extraction routing** — digital PDFs go through fast text extraction; scanned
  pages and images fall back to OCR, and low-quality images are routed to a local
  vision-language model
- **Structured field parsing** — pulls out policyholder name, age, policy number, sum
  insured, premium, dates, room-rent limits, waiting periods, and more
- **Fully local** — no cloud APIs; the LLM runs offline via [Ollama](https://ollama.com)

---

## Project Structure

```
insurance-advisor/
├── app.py                      # Streamlit UI entry point
├── agent/
│   └── tools/
│       └── extractor.py        # Core extraction + field parsing logic
├── utils/
│   ├── file_detector.py        # Detects file format
│   ├── ocr.py                  # Image OCR + quality assessment
│   └── vision.py               # Vision-LLM structured extraction
├── data/                       # Place input documents here (see note below)
├── requirements.txt
└── README.md
```

---

## Requirements

### Python
- Python 3.10+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### External software
Some pip packages are wrappers around external programs that must be installed
separately. These are only needed for the **scanned-PDF / image** path — digital PDFs,
CSV, Excel, and JSON work with the Python packages alone.

| Package         | External dependency | Needed for |
|-----------------|---------------------|------------|
| `pytesseract`   | [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) | OCR on images / scanned PDFs |
| `pdf2image`     | [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) | Converting scanned PDFs to images |
| `langchain-ollama` | [Ollama](https://ollama.com/download) | Vision-LLM extraction |

After installing Ollama, pull the vision model the app uses:
```bash
ollama pull qwen2.5vl:7b
```

---

## Setup & Run

```bash
# 1. Clone
git clone <your-repo-url>
cd insurance-advisor

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

The app opens at `http://localhost:8501`.

> **Note on the `data/` folder:** the app reads input documents from a `data/`
> directory in the project root. If it does not exist, create it (`mkdir data`) and
> drop your insurance documents inside. A `.gitkeep` is committed so the folder is
> present after cloning.

---

## Usage

1. Place one or more documents (`.pdf`, `.jpg`, `.png`, `.csv`, `.xlsx`, `.json`) into `data/`.
2. Launch the app and select a document from the dropdown.
3. Click **Extract Details** to view the parsed policyholder fields.

---

## How It Works

`extract_document()` detects the file format and routes accordingly:

- **Digital PDF** → `pdfplumber` text extraction
- **Scanned PDF** → converted to images (Poppler) → OCR / vision model
- **Image** → quality check → OCR for clean images, vision model for low-quality ones
- **CSV / Excel** → parsed via pandas (with optional name-based row filtering)
- **JSON** → loaded directly

The extracted text is then passed to `parse_insurance_fields()`.

---

## Notes & Roadmap

- Field parsing currently uses a **rule-based (regex) extractor**, which works best on
  documents with predictable label–value formatting. On dense, real-world policy
  documents (tables, multi-line values, varied date formats) accuracy is limited.
- **Planned enhancement:** route extracted text through the bundled `qwen2.5vl:7b`
  vision-language model for structured field extraction, improving robustness across
  document layouts.

---

## Tech Stack

Python · Streamlit · pdfplumber · pandas · pytesseract · pdf2image · OpenCV ·
LangChain · Ollama (`qwen2.5vl:7b`)