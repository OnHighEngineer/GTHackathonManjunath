"""
Data Processing Service
Handles ingestion and transformation of data from various sources
"""

import pandas as pd
import json
import os
from typing import List, Dict, Any, Union
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import random


class DataProcessor:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json', '.sql']
        
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple files and combine data"""
        all_data = []
        metadata = {
            "files_processed": [],
            "total_rows": 0,
            "total_columns": 0,
            "data_types": {},
            "column_stats": {},
            "date_range": None
        }
        
        for path in file_paths:
            df = self._load_file(path)
            if df is not None:
                all_data.append(df)
                metadata["files_processed"].append(os.path.basename(path))
        
        if not all_data:
            raise ValueError("No data could be loaded from the provided files")
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True) if len(all_data) > 1 else all_data[0]
        
        # Generate metadata
        metadata["total_rows"] = len(combined_df)
        metadata["total_columns"] = len(combined_df.columns)
        metadata["columns"] = list(combined_df.columns)
        metadata["data_types"] = {col: str(dtype) for col, dtype in combined_df.dtypes.items()}
        
        # Calculate statistics for numeric columns
        numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            metadata["column_stats"][col] = {
                "mean": float(combined_df[col].mean()) if not pd.isna(combined_df[col].mean()) else 0,
                "median": float(combined_df[col].median()) if not pd.isna(combined_df[col].median()) else 0,
                "std": float(combined_df[col].std()) if not pd.isna(combined_df[col].std()) else 0,
                "min": float(combined_df[col].min()) if not pd.isna(combined_df[col].min()) else 0,
                "max": float(combined_df[col].max()) if not pd.isna(combined_df[col].max()) else 0,
                "sum": float(combined_df[col].sum()) if not pd.isna(combined_df[col].sum()) else 0
            }
        
        # Try to find date columns
        date_cols = combined_df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            date_col = date_cols[0]
            metadata["date_range"] = {
                "start": str(combined_df[date_col].min()),
                "end": str(combined_df[date_col].max())
            }
        
        # Identify categorical columns
        categorical_cols = combined_df.select_dtypes(include=['object', 'category']).columns
        metadata["categorical_columns"] = list(categorical_cols)
        metadata["numeric_columns"] = list(numeric_cols)
        
        # Value counts for categorical columns (top 10)
        for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
            value_counts = combined_df[col].value_counts().head(10).to_dict()
            metadata["column_stats"][col] = {"value_counts": {str(k): int(v) for k, v in value_counts.items()}}
        
        return {
            "dataframe": combined_df,
            "metadata": metadata,
            "summary": combined_df.describe().to_dict()
        }
    
    def _load_file(self, file_path: str) -> Union[pd.DataFrame, None]:
        """Load a single file into a pandas DataFrame"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif ext == '.json':
                df = pd.read_json(file_path)
            else:
                return None
            
            # Try to parse date columns
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            
            return df
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def get_preview(self, file_path: str, rows: int = 10) -> Dict[str, Any]:
        """Get a preview of the data file"""
        df = self._load_file(file_path)
        if df is None:
            return {"error": "Could not load file"}
        
        return {
            "columns": list(df.columns),
            "rows": df.head(rows).to_dict(orient='records'),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def generate_charts(self, processed_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate various charts from the processed data"""
        df = processed_data["dataframe"]
        metadata = processed_data["metadata"]
        charts = {}
        
        # Use absolute path for charts directory
        from config import settings
        output_dir = os.path.join(settings.OUTPUT_FOLDER, "charts")
        os.makedirs(output_dir, exist_ok=True)
        
        numeric_cols = metadata.get("numeric_columns", [])
        categorical_cols = metadata.get("categorical_columns", [])
        
        # 1. Summary statistics bar chart
        if numeric_cols:
            try:
                fig = make_subplots(rows=1, cols=1)
                stats_df = df[numeric_cols[:5]].describe().loc[['mean', 'std', 'min', 'max']]
                
                fig = go.Figure()
                for col in stats_df.columns:
                    fig.add_trace(go.Bar(name=col, x=stats_df.index, y=stats_df[col]))
                
                fig.update_layout(
                    title="Key Metrics Overview",
                    barmode='group',
                    template="plotly_white"
                )
                chart_path = os.path.join(output_dir, "metrics_overview.png")
                fig.write_image(chart_path, width=800, height=500)
                charts["metrics_overview"] = chart_path
            except Exception as e:
                print(f"Error generating metrics chart: {e}")
        
        # 2. Distribution plots for numeric columns
        if len(numeric_cols) >= 1:
            try:
                fig = make_subplots(
                    rows=min(2, len(numeric_cols)), 
                    cols=min(2, len(numeric_cols)),
                    subplot_titles=numeric_cols[:4]
                )
                
                for i, col in enumerate(numeric_cols[:4]):
                    row = i // 2 + 1
                    col_idx = i % 2 + 1
                    fig.add_trace(
                        go.Histogram(x=df[col], name=col, nbinsx=30),
                        row=row, col=col_idx
                    )
                
                fig.update_layout(
                    title="Data Distribution Analysis",
                    showlegend=False,
                    template="plotly_white",
                    height=600
                )
                chart_path = os.path.join(output_dir, "distribution.png")
                fig.write_image(chart_path, width=900, height=600)
                charts["distribution"] = chart_path
            except Exception as e:
                print(f"Error generating distribution chart: {e}")
        
        # 3. Correlation heatmap
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols[:8]].corr()
                
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0
                ))
                
                fig.update_layout(
                    title="Correlation Matrix",
                    template="plotly_white"
                )
                chart_path = os.path.join(output_dir, "correlation.png")
                fig.write_image(chart_path, width=700, height=600)
                charts["correlation"] = chart_path
            except Exception as e:
                print(f"Error generating correlation chart: {e}")
        
        # 4. Category breakdown (pie/bar chart)
        if categorical_cols:
            try:
                cat_col = categorical_cols[0]
                value_counts = df[cat_col].value_counts().head(10)
                
                fig = go.Figure(data=[go.Pie(
                    labels=value_counts.index,
                    values=value_counts.values,
                    hole=0.4
                )])
                
                fig.update_layout(
                    title=f"Distribution by {cat_col}",
                    template="plotly_white"
                )
                chart_path = os.path.join(output_dir, "category_breakdown.png")
                fig.write_image(chart_path, width=700, height=500)
                charts["category_breakdown"] = chart_path
            except Exception as e:
                print(f"Error generating category chart: {e}")
        
        # 5. Trend analysis (if date column exists)
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0 and len(numeric_cols) > 0:
            try:
                date_col = date_cols[0]
                metric_col = numeric_cols[0]
                
                df_sorted = df.sort_values(date_col)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_sorted[date_col],
                    y=df_sorted[metric_col],
                    mode='lines+markers',
                    name=metric_col
                ))
                
                fig.update_layout(
                    title=f"Trend Analysis: {metric_col} over Time",
                    xaxis_title="Date",
                    yaxis_title=metric_col,
                    template="plotly_white"
                )
                chart_path = os.path.join(output_dir, "trend_analysis.png")
                fig.write_image(chart_path, width=900, height=500)
                charts["trend_analysis"] = chart_path
            except Exception as e:
                print(f"Error generating trend chart: {e}")
        
        return charts
    
    def generate_sample_data(self) -> str:
        """Generate sample AdTech data for demonstration"""
        np.random.seed(42)
        
        # Generate dates for the last 30 days
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Campaign data
        campaigns = ['Brand Awareness', 'Lead Generation', 'Retargeting', 'Product Launch', 'Holiday Sale']
        channels = ['Google Ads', 'Facebook', 'Instagram', 'LinkedIn', 'TikTok', 'Twitter']
        regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
        
        data = []
        for date in dates:
            for campaign in campaigns:
                for channel in random.sample(channels, random.randint(2, 4)):
                    impressions = random.randint(10000, 500000)
                    clicks = int(impressions * random.uniform(0.01, 0.05))
                    conversions = int(clicks * random.uniform(0.02, 0.15))
                    spend = round(random.uniform(100, 5000), 2)
                    revenue = round(conversions * random.uniform(20, 200), 2)
                    
                    data.append({
                        'Date': date,
                        'Campaign': campaign,
                        'Channel': channel,
                        'Region': random.choice(regions),
                        'Impressions': impressions,
                        'Clicks': clicks,
                        'Conversions': conversions,
                        'Spend': spend,
                        'Revenue': revenue,
                        'CTR': round(clicks / impressions * 100, 2),
                        'CPC': round(spend / clicks, 2) if clicks > 0 else 0,
                        'ROAS': round(revenue / spend, 2) if spend > 0 else 0
                    })
        
        df = pd.DataFrame(data)
        
        # Save to uploads folder
        os.makedirs("./uploads", exist_ok=True)
        sample_path = "./uploads/sample_adtech_data.csv"
        df.to_csv(sample_path, index=False)
        
        return sample_path
