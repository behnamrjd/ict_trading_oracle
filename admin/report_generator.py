"""
Report Generator for ICT Trading Oracle
"""

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, db_manager):
        self.db = db_manager
        plt.style.use('seaborn-v0_8')
    
    def generate_user_growth_chart(self, days=30):
        """Generate user growth chart"""
        try:
            # Get user registration data for last N days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Mock data (replace with real database query)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            daily_users = [5, 8, 12, 7, 15, 20, 18, 25, 30, 22, 28, 35, 40, 32, 45, 50, 38, 55, 60, 48, 65, 70, 58, 75, 80, 68, 85, 90, 78, 95]
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates[:len(daily_users)], daily_users, marker='o', linewidth=2, markersize=4)
            plt.title('User Growth (Last 30 Days)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('New Users', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating user growth chart: {e}")
            return None
    
    def generate_revenue_chart(self, days=30):
        """Generate revenue chart"""
        try:
            # Mock revenue data
            dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
            daily_revenue = [45000, 52000, 48000, 67000, 71000, 58000, 89000, 95000, 82000, 105000, 
                           112000, 98000, 125000, 135000, 118000, 145000, 158000, 142000, 165000, 175000,
                           162000, 185000, 195000, 178000, 205000, 218000, 195000, 225000, 238000, 215000]
            
            plt.figure(figsize=(12, 6))
            plt.bar(dates[:len(daily_revenue)], daily_revenue, alpha=0.7, color='green')
            plt.title('Daily Revenue (Last 30 Days)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Revenue (Toman)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            # Format y-axis to show values in thousands
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
            
            plt.tight_layout()
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating revenue chart: {e}")
            return None
    
    def generate_signal_accuracy_chart(self, days=30):
        """Generate signal accuracy chart"""
        try:
            # Mock accuracy data
            dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
            accuracy_data = [78, 82, 79, 85, 87, 83, 89, 91, 88, 93, 90, 86, 94, 92, 89, 95, 93, 90, 96, 94,
                           91, 97, 95, 92, 98, 96, 93, 99, 97, 94]
            
            plt.figure(figsize=(12, 6))
            plt.plot(dates[:len(accuracy_data)], accuracy_data, marker='o', linewidth=2, markersize=4, color='blue')
            plt.title('Signal Accuracy (Last 30 Days)', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Accuracy (%)', fontsize=12)
            plt.ylim(70, 100)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            # Add horizontal line for target accuracy
            plt.axhline(y=85, color='red', linestyle='--', alpha=0.7, label='Target (85%)')
            plt.legend()
            
            plt.tight_layout()
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating accuracy chart: {e}")
            return None
    
    def generate_subscription_pie_chart(self):
        """Generate subscription distribution pie chart"""
        try:
            # Get subscription data
            subscription_data = self.db.get_subscription_breakdown() if hasattr(self.db, 'get_subscription_breakdown') else {
                'free': 850, 'premium': 320, 'vip': 80
            }
            
            labels = ['Free', 'Premium', 'VIP']
            sizes = [subscription_data.get('free', 0), subscription_data.get('premium', 0), subscription_data.get('vip', 0)]
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            explode = (0.05, 0.05, 0.1)  # explode VIP slice
            
            plt.figure(figsize=(10, 8))
            plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                   shadow=True, startangle=90)
            plt.title('Subscription Distribution', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating subscription pie chart: {e}")
            return None
    
    def generate_comprehensive_report(self):
        """Generate comprehensive PDF report"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("ICT Trading Oracle - Comprehensive Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Date
            date_para = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
            story.append(date_para)
            story.append(Spacer(1, 12))
            
            # Statistics section
            stats = self.db.get_bot_stats()
            stats_text = f"""
            <b>Key Statistics:</b><br/>
            Total Users: {stats.get('total_users', 0)}<br/>
            Active Users (7 days): {stats.get('active_users', 0)}<br/>
            Total Signals: {stats.get('total_signals', 0)}<br/>
            Daily Signals: {stats.get('daily_signals', 0)}<br/>
            """
            
            stats_para = Paragraph(stats_text, styles['Normal'])
            story.append(stats_para)
            story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return None
