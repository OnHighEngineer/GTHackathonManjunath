# GTHackathon

# 📊 **Automated Insight Engine — H-001 (GroundTruth Mini AI Hackathon)**

### *Data Engineering • ETL • AI Insight Generation • Automated Reporting (PDF/PPTX)*

---

## 🚀 **Overview**

In the AdTech world, Account Managers manually download CSVs, merge data, compute metrics, and create weekly client reports.
This process is **slow**, **error-prone**, and **not scalable** when dealing with terabytes of foot-traffic logs, clickstreams, and weather data.

**The Automated Insight Engine** solves this by providing an **end-to-end automated reporting system** that:

* Ingests structured & unstructured data
* Cleans, transforms, and computes weekly insights
* Generates **AI-powered executive summaries** using **Gemini**
* Exports **beautiful PPTX + PDF reports automatically**
* Requires **zero manual formatting**

This submission fulfills all requirements of **H-001 | The Automated Insight Engine**.

---

## 🏗️ **Architecture**

```
Raw Data Sources (CSV / JSON / SQL / APIs)
               │
               ▼
        Ingestion Layer (ingest.py)
               │
               ▼
     Transform & KPI Engine (transform.py)
               │
               ▼
   AI Insight Generator (Gemini API via insights.py)
               │
               ▼
 Report Generator (PPTX + PDF via report_generator.py)
               │
               ▼
        outputs/weekly_report.pptx
        outputs/weekly_report.pdf
```

---

## ✨ **Features**

### ✅ **1. Multi-source Data Ingestion**

Supports:

* CSV files
* JSON files
* SQLite tables
* Easily extendable to MySQL/Postgres/REST APIs

### ✅ **2. Data Cleaning & Automated KPI Computation**

* Weekly rollups
* Visits, Clicks, CTR
* Missing value handling
* Timestamp normalization

### ✅ **3. AI-powered Executive Summaries (Gemini)**

Uses **Gemini** to generate:

* Business insights
* Performance trends
* Recommendations
* Executive bullet points

### ✅ **4. Automated PPTX + PDF Generation**

* Title slide
* KPI summary slide
* AI insights slide
* Chart slide
* Downloadable PDF version

### ✅ **5. Fully Scripted Pipeline (No UI required)**

One command generates the entire report:

```bash
python app.py
```

---

## 📁 **Project Structure**

```
automated_insight_engine/
├── app.py
├── ingest.py
├── transform.py
├── insights.py
├── report_generator.py
│
├── requirements.txt
├── README.md
├── .env.example
│
├── example_data/
│   └── visits.csv
│
└── outputs/
    ├── weekly_report.pptx
    └── weekly_report.pdf
```

---

## ⚙️ **Installation**

### 1️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 **Environment Setup**

Create a `.env` file:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
OUTPUT_DIR=./outputs
```

---

## ▶️ **Run the Pipeline**

Using the sample CSV:

```bash
python app.py
```

Output files:

```
outputs/weekly_report.pptx
outputs/weekly_report.pdf
```

---

## 💡 **Example Output (Slides Included)**

 PPTX contains:

* Title slide
* KPI metrics slide
* AI insights slide
* Chart slide

 PDF contains:

* A summary + pointer to the PPTX

---

## 🔒 **Privacy & Security**

* No raw user PII is sent to Gemini
* Only aggregated KPIs or masked snippets are sent
* Supports enterprise-safe deployment

---

## 🛠️ **Tech Stack**

* **Python** (Pandas, Polars)
* **Gemini Generative AI**
* **python-pptx** for PPT generation
* **ReportLab** for PDF generation
* **Matplotlib** for visualizations
* **dotenv**, **requests**, **SQLAlchemy**

---

## 🚧 **Future Improvements**

* High-fidelity PDF (LibreOffice headless export)
* Dashboard preview before exporting
* Multi-file ingestion with scheduling
* Integration with BigQuery/Snowflake

