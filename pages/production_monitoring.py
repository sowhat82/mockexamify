"""
Production Monitoring Dashboard - Real-time system monitoring and alerts
Comprehensive system health, performance metrics, and operational insights
"""
import streamlit as st
import asyncio
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import production utilities
from production_utils import (
    production_cache, performance_monitor, health_checker, 
    audit_logger, LOGGERS, get_production_metrics
)
from auth_utils import verify_admin_access

def show_production_monitoring():
    """Main production monitoring dashboard"""
    # Verify admin access
    if not verify_admin_access():
        st.error("⛔ Access denied. Admin privileges required.")
        return
    
    st.header("🔧 Production Monitoring Dashboard")
    st.markdown("Real-time system health, performance metrics, and operational insights")
    
    # Auto-refresh option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📊 System Status Overview")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.experimental_rerun()
    
    # Get current metrics
    health_status = health_checker.get_overall_health()
    production_metrics = get_production_metrics()
    
    # Status overview cards
    render_status_overview(health_status)
    
    # Create tabs for different monitoring views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏥 Health", 
        "⚡ Performance", 
        "💾 Cache", 
        "📋 Logs",
        "🔔 Alerts"
    ])
    
    with tab1:
        render_health_monitoring(health_status)
    
    with tab2:
        render_performance_monitoring(production_metrics)
    
    with tab3:
        render_cache_monitoring(production_metrics['cache_stats'])
    
    with tab4:
        render_log_monitoring()
    
    with tab5:
        render_alerts_monitoring()

def render_status_overview(health_status: Dict[str, Any]):
    """Render system status overview cards"""
    overall_status = health_status['overall_status']
    components = health_status['components']
    
    # Status indicator
    status_color = "#28a745" if overall_status == 'healthy' else "#ffc107" if overall_status == 'degraded' else "#dc3545"
    status_icon = "✅" if overall_status == 'healthy' else "⚠️" if overall_status == 'degraded' else "❌"
    
    st.markdown(f"""
    <div style="
        background: {status_color}20;
        border-left: 4px solid {status_color};
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
        text-align: center;
    ">
        <h2 style="color: {status_color}; margin: 0;">
            {status_icon} System Status: {overall_status.title()}
        </h2>
        <p style="margin: 0.5rem 0 0 0; color: #666;">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Component status cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_status = components['database']['status']
        db_color = "#28a745" if db_status == 'healthy' else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border: 1px solid {db_color}; border-radius: 8px;">
            <h4 style="color: {db_color}; margin: 0;">🗄️ Database</h4>
            <p style="margin: 0.5rem 0 0 0;">{db_status.title()}</p>
            <small>{components['database'].get('response_time_ms', 0)}ms</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        ai_status = components['ai_service']['status']
        ai_color = "#28a745" if ai_status == 'healthy' else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border: 1px solid {ai_color}; border-radius: 8px;">
            <h4 style="color: {ai_color}; margin: 0;">🤖 AI Service</h4>
            <p style="margin: 0.5rem 0 0 0;">{ai_status.title()}</p>
            <small>{components['ai_service'].get('response_time_ms', 0)}ms</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cpu_usage = components['system'].get('cpu_percent', 0)
        cpu_color = "#28a745" if cpu_usage < 70 else "#ffc107" if cpu_usage < 85 else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border: 1px solid {cpu_color}; border-radius: 8px;">
            <h4 style="color: {cpu_color}; margin: 0;">💻 CPU</h4>
            <p style="margin: 0.5rem 0 0 0;">{cpu_usage:.1f}%</p>
            <small>System Load</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        memory_usage = components['system'].get('memory_percent', 0)
        memory_color = "#28a745" if memory_usage < 70 else "#ffc107" if memory_usage < 85 else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; border: 1px solid {memory_color}; border-radius: 8px;">
            <h4 style="color: {memory_color}; margin: 0;">🧠 Memory</h4>
            <p style="margin: 0.5rem 0 0 0;">{memory_usage:.1f}%</p>
            <small>RAM Usage</small>
        </div>
        """, unsafe_allow_html=True)

def render_health_monitoring(health_status: Dict[str, Any]):
    """Render detailed health monitoring"""
    st.subheader("🏥 System Health Details")
    
    components = health_status['components']
    
    # Database health
    st.write("**🗄️ Database Health**")
    db_health = components['database']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", db_health['status'].title())
    with col2:
        st.metric("Response Time", f"{db_health.get('response_time_ms', 0)}ms")
    with col3:
        st.metric("Connections", db_health.get('connections', 0))
    
    # AI Service health
    st.write("**🤖 AI Service Health**")
    ai_health = components['ai_service']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status", ai_health['status'].title())
    with col2:
        st.metric("Response Time", f"{ai_health.get('response_time_ms', 0)}ms")
    with col3:
        st.metric("Rate Limit", f"{ai_health.get('rate_limit_remaining', 0)} remaining")
    
    # System resources
    st.write("**💻 System Resources**")
    system_stats = components['system']
    
    if system_stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_percent = system_stats.get('cpu_percent', 0)
            st.metric("CPU Usage", f"{cpu_percent:.1f}%", 
                     delta="High" if cpu_percent > 80 else "Normal")
        
        with col2:
            memory_percent = system_stats.get('memory_percent', 0)
            st.metric("Memory Usage", f"{memory_percent:.1f}%",
                     delta="High" if memory_percent > 80 else "Normal")
        
        with col3:
            disk_usage = system_stats.get('disk_usage', 0)
            st.metric("Disk Usage", f"{disk_usage:.1f}%",
                     delta="High" if disk_usage > 90 else "Normal")
    
    # Health check history (simulated)
    st.write("**📈 Health Trends (Last 24 Hours)**")
    
    # Generate sample health data
    hours = 24
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
    
    # Simulate health scores (0-100)
    db_scores = [95 + (i % 5) for i in range(hours)]
    ai_scores = [90 + (i % 10) for i in range(hours)]
    system_scores = [85 + (i % 15) for i in range(hours)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps, y=db_scores,
        mode='lines+markers',
        name='Database Health',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps, y=ai_scores,
        mode='lines+markers',
        name='AI Service Health',
        line=dict(color='green')
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps, y=system_scores,
        mode='lines+markers',
        name='System Health',
        line=dict(color='orange')
    ))
    
    fig.update_layout(
        title="Health Score Trends",
        xaxis_title="Time",
        yaxis_title="Health Score (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_performance_monitoring(production_metrics: Dict[str, Any]):
    """Render performance monitoring dashboard"""
    st.subheader("⚡ Performance Metrics")
    
    # Response time metrics
    st.write("**📊 Response Time Analysis**")
    
    # Generate sample response time data
    functions = ['User Login', 'Exam Loading', 'AI Generation', 'Database Query', 'File Upload']
    avg_times = [120, 250, 1500, 80, 800]  # milliseconds
    p95_times = [200, 400, 2500, 150, 1200]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Average Response Times', 'P95 Response Times'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Bar(x=functions, y=avg_times, name='Avg Time (ms)', marker_color='skyblue'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=functions, y=p95_times, name='P95 Time (ms)', marker_color='lightcoral'),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance trends over time
    st.write("**📈 Performance Trends (Last 6 Hours)**")
    
    # Generate sample performance data
    hours = 6
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
    
    # Simulate performance metrics
    response_times = [150 + (i * 10) + (i % 3 * 20) for i in range(hours)]
    throughput = [50 + (i * 5) + (i % 2 * 10) for i in range(hours)]
    error_rates = [0.5 + (i % 4 * 0.2) for i in range(hours)]
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Response Time (ms)', 'Throughput (req/min)', 'Error Rate (%)'),
        vertical_spacing=0.08
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=response_times, mode='lines+markers', 
                  name='Response Time', line=dict(color='blue')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=throughput, mode='lines+markers',
                  name='Throughput', line=dict(color='green')),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=error_rates, mode='lines+markers',
                  name='Error Rate', line=dict(color='red')),
        row=3, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top slow operations
    st.write("**🐌 Slowest Operations (Last Hour)**")
    
    slow_ops = [
        {'operation': 'AI Question Generation', 'avg_time': 2.3, 'count': 15},
        {'operation': 'PDF Generation', 'avg_time': 1.8, 'count': 8},
        {'operation': 'Database Migration', 'avg_time': 1.2, 'count': 3},
        {'operation': 'File Upload Processing', 'avg_time': 0.9, 'count': 25},
        {'operation': 'User Analytics Calculation', 'avg_time': 0.7, 'count': 42}
    ]
    
    df = pd.DataFrame(slow_ops)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        fig = px.bar(df, x='operation', y='avg_time', 
                    title='Average Response Time by Operation',
                    labels={'avg_time': 'Avg Time (s)', 'operation': 'Operation'})
        fig.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def render_cache_monitoring(cache_stats: Dict[str, Any]):
    """Render cache performance monitoring"""
    st.subheader("💾 Cache Performance")
    
    # Cache overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cache Size", f"{cache_stats['size']}/{cache_stats['max_size']}")
    
    with col2:
        st.metric("Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
    
    with col3:
        st.metric("Memory Usage", cache_stats['memory_usage'])
    
    with col4:
        utilization = (cache_stats['size'] / cache_stats['max_size']) * 100
        st.metric("Utilization", f"{utilization:.1f}%")
    
    # Cache hit/miss visualization
    st.write("**📊 Cache Performance**")
    
    # Cache hit rate pie chart
    fig = px.pie(
        values=[cache_stats['hit_count'], cache_stats['miss_count']],
        names=['Hits', 'Misses'],
        title="Cache Hit/Miss Ratio",
        color_discrete_map={'Hits': '#28a745', 'Misses': '#dc3545'}
    )
    fig.update_layout(height=300)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cache operations over time (simulated)
        hours = 12
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours, 0, -1)]
        hit_rates = [85 + (i % 4 * 5) for i in range(hours)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps, y=hit_rates,
            mode='lines+markers',
            name='Hit Rate %',
            line=dict(color='green')
        ))
        
        fig.update_layout(
            title="Cache Hit Rate Trend",
            xaxis_title="Time",
            yaxis_title="Hit Rate (%)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Cache management actions
    st.write("**🔧 Cache Management**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear All Cache", type="secondary"):
            production_cache.invalidate()
            st.success("Cache cleared successfully!")
            st.experimental_rerun()
    
    with col2:
        if st.button("🧹 Clear AI Cache", type="secondary"):
            production_cache.invalidate("ai_")
            st.success("AI cache cleared!")
            st.experimental_rerun()
    
    with col3:
        if st.button("📊 Clear Analytics Cache", type="secondary"):
            production_cache.invalidate("analytics_")
            st.success("Analytics cache cleared!")
            st.experimental_rerun()
    
    # Cache statistics table
    st.write("**📈 Detailed Cache Statistics**")
    
    cache_details = [
        {"Metric": "Total Requests", "Value": cache_stats['hit_count'] + cache_stats['miss_count']},
        {"Metric": "Cache Hits", "Value": cache_stats['hit_count']},
        {"Metric": "Cache Misses", "Value": cache_stats['miss_count']},
        {"Metric": "Hit Rate", "Value": f"{cache_stats['hit_rate']:.2f}%"},
        {"Metric": "Current Size", "Value": cache_stats['size']},
        {"Metric": "Max Size", "Value": cache_stats['max_size']},
        {"Metric": "Memory Usage", "Value": cache_stats['memory_usage']},
    ]
    
    st.dataframe(pd.DataFrame(cache_details), use_container_width=True)

def render_log_monitoring():
    """Render log monitoring and analysis"""
    st.subheader("📋 System Logs")
    
    # Log level filter
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_logger = st.selectbox(
            "Select Log Category",
            ["All", "Performance", "Security", "User Activity", "AI Operations", "Database", "Payment"]
        )
    
    with col2:
        log_level = st.selectbox("Log Level", ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    
    with col3:
        time_range = st.selectbox("Time Range", ["Last Hour", "Last 6 Hours", "Last Day"])
    
    # Simulated log entries
    st.write("**📄 Recent Log Entries**")
    
    sample_logs = [
        {
            "timestamp": "2024-01-15 10:30:15",
            "level": "INFO",
            "logger": "user_activity",
            "message": "User student@test.com completed practice session"
        },
        {
            "timestamp": "2024-01-15 10:29:42",
            "level": "INFO", 
            "logger": "performance",
            "message": "AI question generation completed in 1.2s"
        },
        {
            "timestamp": "2024-01-15 10:28:30",
            "level": "WARNING",
            "logger": "security",
            "message": "Rate limit warning for IP 192.168.1.100"
        },
        {
            "timestamp": "2024-01-15 10:27:15",
            "level": "ERROR",
            "logger": "database",
            "message": "Query timeout on user analytics query"
        },
        {
            "timestamp": "2024-01-15 10:26:00",
            "level": "INFO",
            "logger": "ai_operations",
            "message": "Successfully generated 10 question variants"
        }
    ]
    
    # Filter logs based on selection
    filtered_logs = sample_logs
    if selected_logger != "All":
        filtered_logs = [log for log in filtered_logs if log['logger'] == selected_logger.lower().replace(' ', '_')]
    if log_level != "All":
        filtered_logs = [log for log in filtered_logs if log['level'] == log_level]
    
    # Display logs with color coding
    for log in filtered_logs:
        level_color = {
            "DEBUG": "#6c757d",
            "INFO": "#007bff", 
            "WARNING": "#ffc107",
            "ERROR": "#dc3545",
            "CRITICAL": "#6f42c1"
        }.get(log['level'], "#000000")
        
        st.markdown(f"""
        <div style="
            border-left: 3px solid {level_color};
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
            background: #f8f9fa;
            font-family: monospace;
            font-size: 0.9rem;
        ">
            <span style="color: #6c757d;">{log['timestamp']}</span>
            <span style="color: {level_color}; font-weight: bold; margin: 0 1rem;">[{log['level']}]</span>
            <span style="color: #495057; font-style: italic;">{log['logger']}</span><br>
            <span style="color: #212529;">{log['message']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Log statistics
    st.write("**📊 Log Statistics (Last 24 Hours)**")
    
    log_stats = [
        {"Level": "INFO", "Count": 1247, "Percentage": "78.2%"},
        {"Level": "WARNING", "Count": 156, "Percentage": "9.8%"},
        {"Level": "ERROR", "Count": 89, "Percentage": "5.6%"},
        {"Level": "DEBUG", "Count": 98, "Percentage": "6.2%"},
        {"Level": "CRITICAL", "Count": 3, "Percentage": "0.2%"}
    ]
    
    df = pd.DataFrame(log_stats)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        fig = px.pie(df, values='Count', names='Level', 
                    title='Log Level Distribution')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def render_alerts_monitoring():
    """Render alerts and notifications"""
    st.subheader("🔔 System Alerts & Notifications")
    
    # Current alerts
    st.write("**🚨 Active Alerts**")
    
    current_alerts = [
        {
            "severity": "WARNING",
            "message": "High memory usage detected (82%)",
            "timestamp": "2024-01-15 10:25:00",
            "component": "System"
        },
        {
            "severity": "INFO", 
            "message": "Scheduled backup completed successfully",
            "timestamp": "2024-01-15 09:00:00",
            "component": "Database"
        }
    ]
    
    for alert in current_alerts:
        severity_color = {
            "CRITICAL": "#dc3545",
            "WARNING": "#ffc107", 
            "INFO": "#007bff",
            "SUCCESS": "#28a745"
        }.get(alert['severity'], "#6c757d")
        
        severity_icon = {
            "CRITICAL": "🚨",
            "WARNING": "⚠️",
            "INFO": "ℹ️", 
            "SUCCESS": "✅"
        }.get(alert['severity'], "📢")
        
        st.markdown(f"""
        <div style="
            border: 1px solid {severity_color};
            border-left: 4px solid {severity_color};
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            background: {severity_color}10;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.2rem;">{severity_icon}</span>
                    <strong style="color: {severity_color}; margin-left: 0.5rem;">{alert['severity']}</strong>
                    <span style="margin-left: 1rem;">{alert['message']}</span>
                </div>
                <div style="text-align: right; color: #6c757d; font-size: 0.9rem;">
                    <div>{alert['component']}</div>
                    <div>{alert['timestamp']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Alert configuration
    st.write("**⚙️ Alert Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**System Thresholds**")
        cpu_threshold = st.slider("CPU Alert Threshold (%)", 50, 95, 80)
        memory_threshold = st.slider("Memory Alert Threshold (%)", 50, 95, 85)
        response_threshold = st.slider("Response Time Alert (ms)", 500, 5000, 2000)
    
    with col2:
        st.write("**Notification Settings**")
        email_alerts = st.checkbox("Email Alerts", value=True)
        slack_alerts = st.checkbox("Slack Notifications", value=False)
        sms_alerts = st.checkbox("SMS Alerts (Critical Only)", value=False)
        
        if st.button("💾 Save Alert Settings"):
            st.success("Alert settings saved!")
    
    # Alert history
    st.write("**📈 Alert History (Last 7 Days)**")
    
    # Generate sample alert history
    days = 7
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
    critical_counts = [0, 1, 0, 0, 2, 0, 0]
    warning_counts = [3, 5, 2, 4, 8, 1, 2]
    info_counts = [15, 18, 12, 16, 22, 8, 14]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates, y=critical_counts,
        name='Critical',
        marker_color='#dc3545'
    ))
    
    fig.add_trace(go.Bar(
        x=dates, y=warning_counts,
        name='Warning',
        marker_color='#ffc107'
    ))
    
    fig.add_trace(go.Bar(
        x=dates, y=info_counts,
        name='Info',
        marker_color='#007bff'
    ))
    
    fig.update_layout(
        title="Daily Alert Counts",
        xaxis_title="Date",
        yaxis_title="Number of Alerts",
        barmode='stack',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Main entry point
if __name__ == "__main__":
    show_production_monitoring()