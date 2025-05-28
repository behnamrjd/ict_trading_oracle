"""
Real-time System Monitor for ICT Trading Oracle
"""

import asyncio
import psutil
import time
import logging
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, db_manager, api_manager):
        self.db = db_manager
        self.api = api_manager
        self.monitoring = False
        self.alerts = []
        self.metrics_history = []
        
    async def start_monitoring(self, interval=60):
        """Start continuous system monitoring"""
        print("🔍 Starting System Monitoring...")
        self.monitoring = True
        
        while self.monitoring:
            try:
                # Collect metrics
                metrics = await self._collect_real_time_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if datetime.fromisoformat(m['timestamp']) > cutoff_time
                ]
                
                # Check for alerts
                alerts = self._check_alert_conditions(metrics)
                if alerts:
                    self.alerts.extend(alerts)
                    await self._handle_alerts(alerts)
                
                # Log metrics
                self._log_metrics(metrics)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        print("🛑 System monitoring stopped")
    
    async def _collect_real_time_metrics(self):
        """Collect real-time system metrics"""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()
        
        # Database metrics
        db_start = time.time()
        try:
            stats = self.db.get_bot_stats()
            db_response_time = time.time() - db_start
            db_available = True
        except Exception as e:
            db_response_time = None
            db_available = False
            logger.error(f"Database check failed: {e}")
        
        # API metrics
        api_start = time.time()
        try:
            price_data = self.api.get_gold_price()
            api_response_time = time.time() - api_start
            api_available = price_data is not None
        except Exception as e:
            api_response_time = None
            api_available = False
            logger.error(f"API check failed: {e}")
        
        return {
            'timestamp': timestamp.isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv
            },
            'process': {
                'cpu_percent': process_cpu,
                'memory_mb': process_memory.rss / (1024**2),
                'memory_percent': (process_memory.rss / memory.total) * 100,
                'threads': process.num_threads()
            },
            'database': {
                'available': db_available,
                'response_time': db_response_time,
                'total_users': stats.get('total_users', 0) if db_available else 0,
                'total_signals': stats.get('total_signals', 0) if db_available else 0
            },
            'api': {
                'available': api_available,
                'response_time': api_response_time
            }
        }
    
    def _check_alert_conditions(self, metrics):
        """Check for alert conditions"""
        alerts = []
        timestamp = metrics['timestamp']
        
        # CPU alert
        if metrics['system']['cpu_percent'] > 90:
            alerts.append({
                'type': 'CPU_HIGH',
                'severity': 'CRITICAL',
                'message': f"CPU usage is {metrics['system']['cpu_percent']:.1f}%",
                'value': metrics['system']['cpu_percent'],
                'threshold': 90,
                'timestamp': timestamp
            })
        elif metrics['system']['cpu_percent'] > 75:
            alerts.append({
                'type': 'CPU_WARNING',
                'severity': 'WARNING',
                'message': f"CPU usage is {metrics['system']['cpu_percent']:.1f}%",
                'value': metrics['system']['cpu_percent'],
                'threshold': 75,
                'timestamp': timestamp
            })
        
        # Memory alert
        if metrics['system']['memory_percent'] > 95:
            alerts.append({
                'type': 'MEMORY_CRITICAL',
                'severity': 'CRITICAL',
                'message': f"Memory usage is {metrics['system']['memory_percent']:.1f}%",
                'value': metrics['system']['memory_percent'],
                'threshold': 95,
                'timestamp': timestamp
            })
        elif metrics['system']['memory_percent'] > 85:
            alerts.append({
                'type': 'MEMORY_WARNING',
                'severity': 'WARNING',
                'message': f"Memory usage is {metrics['system']['memory_percent']:.1f}%",
                'value': metrics['system']['memory_percent'],
                'threshold': 85,
                'timestamp': timestamp
            })
        
        # Disk space alert
        if metrics['system']['disk_percent'] > 95:
            alerts.append({
                'type': 'DISK_CRITICAL',
                'severity': 'CRITICAL',
                'message': f"Disk usage is {metrics['system']['disk_percent']:.1f}%",
                'value': metrics['system']['disk_percent'],
                'threshold': 95,
                'timestamp': timestamp
            })
        
        # Database alert
        if not metrics['database']['available']:
            alerts.append({
                'type': 'DATABASE_DOWN',
                'severity': 'CRITICAL',
                'message': "Database is not available",
                'timestamp': timestamp
            })
        elif metrics['database']['response_time'] and metrics['database']['response_time'] > 5:
            alerts.append({
                'type': 'DATABASE_SLOW',
                'severity': 'WARNING',
                'message': f"Database response time is {metrics['database']['response_time']:.2f}s",
                'value': metrics['database']['response_time'],
                'threshold': 5,
                'timestamp': timestamp
            })
        
        # API alert
        if not metrics['api']['available']:
            alerts.append({
                'type': 'API_DOWN',
                'severity': 'CRITICAL',
                'message': "External APIs are not available",
                'timestamp': timestamp
            })
        elif metrics['api']['response_time'] and metrics['api']['response_time'] > 10:
            alerts.append({
                'type': 'API_SLOW',
                'severity': 'WARNING',
                'message': f"API response time is {metrics['api']['response_time']:.2f}s",
                'value': metrics['api']['response_time'],
                'threshold': 10,
                'timestamp': timestamp
            })
        
        return alerts
    
    async def _handle_alerts(self, alerts):
        """Handle system alerts"""
        for alert in alerts:
            severity_emoji = "🔥" if alert['severity'] == 'CRITICAL' else "⚠️"
            print(f"{severity_emoji} ALERT: {alert['message']}")
            
            # Log alert
            logger.warning(f"System Alert: {alert}")
            
            # Here you could implement:
            # - Send notification to admin
            # - Auto-scaling actions
            # - Emergency procedures
    
    def _log_metrics(self, metrics):
        """Log metrics to file"""
        try:
            log_dir = "monitoring_logs"
            os.makedirs(log_dir, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = f"{log_dir}/metrics_{date_str}.jsonl"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metrics) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def get_monitoring_dashboard(self):
        """Get monitoring dashboard data"""
        if not self.metrics_history:
            return None
        
        latest_metrics = self.metrics_history[-1]
        
        # Calculate trends (last hour vs current)
        hour_ago = datetime.now() - timedelta(hours=1)
        hour_ago_metrics = None
        
        for metrics in reversed(self.metrics_history):
            if datetime.fromisoformat(metrics['timestamp']) <= hour_ago:
                hour_ago_metrics = metrics
                break
        
        trends = {}
        if hour_ago_metrics:
            trends = {
                'cpu_trend': latest_metrics['system']['cpu_percent'] - hour_ago_metrics['system']['cpu_percent'],
                'memory_trend': latest_metrics['system']['memory_percent'] - hour_ago_metrics['system']['memory_percent'],
                'db_trend': (latest_metrics['database']['response_time'] or 0) - (hour_ago_metrics['database']['response_time'] or 0)
            }
        
        # Recent alerts (last 24 hours)
        recent_alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'current_metrics': latest_metrics,
            'trends': trends,
            'recent_alerts': recent_alerts,
            'alert_count': {
                'critical': len([a for a in recent_alerts if a['severity'] == 'CRITICAL']),
                'warning': len([a for a in recent_alerts if a['severity'] == 'WARNING'])
            },
            'uptime': self._calculate_uptime(),
            'health_score': self._calculate_health_score(latest_metrics)
        }
    
    def _calculate_uptime(self):
        """Calculate system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            return f"{uptime_hours:.1f} hours"
        except:
            return "Unknown"
    
    def _calculate_health_score(self, metrics):
        """Calculate overall system health score (0-100)"""
        try:
            score = 100
            
            # CPU penalty
            if metrics['system']['cpu_percent'] > 90:
                score -= 30
            elif metrics['system']['cpu_percent'] > 75:
                score -= 15
            
            # Memory penalty
            if metrics['system']['memory_percent'] > 95:
                score -= 30
            elif metrics['system']['memory_percent'] > 85:
                score -= 15
            
            # Database penalty
            if not metrics['database']['available']:
                score -= 40
            elif metrics['database']['response_time'] and metrics['database']['response_time'] > 5:
                score -= 20
            
            # API penalty
            if not metrics['api']['available']:
                score -= 20
            elif metrics['api']['response_time'] and metrics['api']['response_time'] > 10:
                score -= 10
            
            return max(0, score)
            
        except:
            return 50
