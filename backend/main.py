"""
Automated Insight Engine - Main FastAPI Application
Ingests data, generates AI insights, and exports PDF/PPTX reports
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from services.data_processor import DataProcessor
from services.insight_generator import insight_generator
from services.report_generator import ReportGenerator
from config import settings
# In main.py - only the import section
from services.data_processor import DataProcessor
from services.insight_generator import insight_generator  # Import the instance, not the class
from services.report_generator import ReportGenerator
from config import settings

# Initialize services
data_processor = DataProcessor()
# insight_generator is already an instance from the import above
report_generator = ReportGenerator()
app = FastAPI(
    title="Automated Insight Engine",
    description="AI-powered data analysis and report generation system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.OUTPUT_FOLDER, exist_ok=True)

# Initialize services
data_processor = DataProcessor()
# insight_generator is already imported as an instance from the module
report_generator = ReportGenerator()

# In-memory job storage (use Redis/DB in production)
jobs = {}


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int
    message: str
    report_url: Optional[str] = None
    insights: Optional[dict] = None


class ReportConfig(BaseModel):
    title: str = "Weekly Performance Report"
    company_name: str = "Company"
    report_type: str = "pdf"  # "pdf" or "pptx"
    include_charts: bool = True
    include_summary: bool = True
    include_recommendations: bool = True


@app.get("/")
async def root():
    return {"message": "Automated Insight Engine API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload one or more data files (CSV, Excel, JSON)"""
    uploaded_files = []
    
    for file in files:
        # Validate file type
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json', '.sql']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )
        
        # Save file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_FOLDER, f"{file_id}{file_ext}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        uploaded_files.append({
            "file_id": file_id,
            "original_name": file.filename,
            "file_path": file_path,
            "file_type": file_ext
        })
    
    return {"uploaded_files": uploaded_files, "count": len(uploaded_files)}


@app.post("/api/analyze")
async def analyze_data(
    file_ids: List[str],
    config: ReportConfig
):
    """Start analysis job for uploaded files"""
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job queued for processing"
    )
    
    # Start background processing using asyncio.create_task
    asyncio.create_task(
        process_analysis_job(
            job_id=job_id,
            file_ids=file_ids,
            config=config
        )
    )
    
    return {"job_id": job_id, "status": "pending"}


async def process_analysis_job(job_id: str, file_ids: List[str], config: ReportConfig):
    """Background task to process data and generate report"""
    try:
        # Update status
        jobs[job_id].status = "processing"
        jobs[job_id].progress = 10
        jobs[job_id].message = "Loading data files..."
        
        # Find uploaded files
        file_paths = []
        for fid in file_ids:
            for ext in ['.csv', '.xlsx', '.xls', '.json', '.sql']:
                path = os.path.join(settings.UPLOAD_FOLDER, f"{fid}{ext}")
                print(f"Checking path: {path}")
                if os.path.exists(path):
                    file_paths.append(path)
                    print(f"Found file: {path}")
                    break
        
        if not file_paths:
            raise Exception(f"No valid files found for IDs: {file_ids}")
        
        print(f"Processing files: {file_paths}")
        
        # Process data
        jobs[job_id].progress = 25
        jobs[job_id].message = "Processing and transforming data..."
        
        processed_data = data_processor.process_files(file_paths)
        print(f"Data processed: {processed_data['metadata'].get('total_rows', 0)} rows")
        
        # Generate AI insights
        jobs[job_id].progress = 50
        jobs[job_id].message = "Generating AI-powered insights..."
        
        insights = await insight_generator.generate_insights(processed_data)
        print("Insights generated")
        
        # Generate charts
        jobs[job_id].progress = 70
        jobs[job_id].message = "Creating visualizations..."
        
        charts = data_processor.generate_charts(processed_data)
        print(f"Charts generated: {list(charts.keys())}")
        
        # Generate report
        jobs[job_id].progress = 85
        jobs[job_id].message = f"Generating {config.report_type.upper()} report..."
        
        report_path = report_generator.generate_report(
            data=processed_data,
            insights=insights,
            charts=charts,
            config=config.model_dump(),
            job_id=job_id
        )
        print(f"Report generated: {report_path}")
        
        # Complete
        jobs[job_id].status = "completed"
        jobs[job_id].progress = 100
        jobs[job_id].message = "Report generated successfully!"
        jobs[job_id].report_url = f"/api/reports/{job_id}/{config.report_type}"
        jobs[job_id].insights = insights
        
    except Exception as e:
        import traceback
        print(f"Error in job {job_id}: {str(e)}")
        traceback.print_exc()
        jobs[job_id].status = "failed"
        jobs[job_id].message = f"Error: {str(e)}"


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an analysis job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/reports/{job_id}/{report_type}")
async def download_report(job_id: str, report_type: str):
    """Download generated report"""
    filename = f"{job_id}.{report_type}"
    file_path = os.path.join(settings.OUTPUT_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    media_type = "application/pdf" if report_type == "pdf" else \
                 "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=f"insight_report.{report_type}"
    )


@app.post("/api/preview")
async def preview_data(file_ids: List[str]):
    """Get a preview of uploaded data"""
    previews = []
    
    for fid in file_ids:
        for ext in ['.csv', '.xlsx', '.xls', '.json']:
            path = os.path.join(settings.UPLOAD_FOLDER, f"{fid}{ext}")
            if os.path.exists(path):
                preview = data_processor.get_preview(path)
                previews.append({
                    "file_id": fid,
                    "preview": preview
                })
                break
    
    return {"previews": previews}


@app.get("/api/sample-data")
async def get_sample_data():
    """Generate sample data for demo"""
    sample_path = data_processor.generate_sample_data()
    return {"message": "Sample data generated", "path": sample_path}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)