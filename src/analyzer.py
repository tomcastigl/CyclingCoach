import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# Set default theme for all plots
px.defaults.template = "plotly_dark"

class ActivityAnalyzer:
    def __init__(self, data_file='data/activities.csv'):
        """Initialize the analyzer with a data file"""
        if os.path.exists(data_file):
            self.df = pd.read_csv(data_file)
            # Convert date string to datetime
            if 'start_date_local' in self.df.columns:
                self.df['start_date_local'] = pd.to_datetime(self.df['start_date_local'])
            print(f"Loaded {len(self.df)} activities from {data_file}")
        else:
            self.df = None
            print(f"Data file {data_file} not found")
    
    def filter_activity_type(self, activity_type='Ride'):
        """Filter activities by type"""
        if self.df is None:
            return None
        
        return self.df[self.df['type'] == activity_type]
    
    def summary_stats(self, df=None):
        """Calculate summary statistics for activities"""
        if df is None:
            df = self.df
        
        if df is None or len(df) == 0:
            print("No activities available for analysis")
            return None
        
        # Weekly summary
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        # Handle timezone-aware datetime comparison
        if 'start_date_local' in df.columns:
            # Convert to pandas Timestamp for consistent handling
            week_ago_ts = pd.Timestamp(week_ago)
            
            # Check if start_date_local column has timezone info
            if hasattr(df['start_date_local'].dtype, 'tz') and df['start_date_local'].dtype.tz is not None:
                # Convert week_ago to timezone-aware
                week_ago_ts = week_ago_ts.tz_localize('UTC')
            
            # Filter data
            week_df = df[df['start_date_local'] >= week_ago_ts]
        else:
            week_df = pd.DataFrame()  # Empty dataframe if no date column
        
        stats = {
            'total_activities': len(df),
            'activities_past_week': len(week_df),
            'total_distance_km': df['distance'].sum() / 1000 if 'distance' in df.columns else 0,
            'total_elevation_m': df['total_elevation_gain'].sum() if 'total_elevation_gain' in df.columns else 0,
            'total_moving_time_h': df['moving_time'].sum() / 3600 if 'moving_time' in df.columns else 0,
            'avg_heartrate': df['average_heartrate'].mean() if 'average_heartrate' in df.columns else 0,
            'max_heartrate': df['max_heartrate'].max() if 'max_heartrate' in df.columns else 0,
            'avg_speed_kmh': (df['average_speed'].mean() * 3.6) if 'average_speed' in df.columns else 0,
            'max_speed_kmh': (df['max_speed'].max() * 3.6) if 'max_speed' in df.columns else 0,
            'avg_watts': df['average_watts'].mean() if 'average_watts' in df.columns else 0,
            'max_watts': df['max_watts'].max() if 'max_watts' in df.columns else 0,
        }
        
        return stats
    
    def plot_weekly_distance(self, activity_type=None):
        """Plot weekly distance for activities"""
        if self.df is None:
            return
        
        df = self.filter_activity_type(activity_type) if activity_type else self.df
        
        # Only show weekly distance if we have at least 1 month of data
        if (pd.to_datetime(df['start_date_local'].max()) - pd.to_datetime(df['start_date_local'].min())).days < 30:
            return
            
        # Convert to datetime and set as index
        df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        df.set_index('start_date_local', inplace=True)
        
        # Resample to weekly and sum distances
        weekly_distance = df['distance'].resample('W').sum()
        
        # Create the plot
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=weekly_distance.index,
            y=weekly_distance.values,
            name='Weekly Distance'
        ))
        
        fig.update_layout(
            title='Weekly Ride Distance',
            xaxis_title='Week',
            yaxis_title='Distance (km)',
            template='plotly_dark',
            height=600,
            width=1000
        )
        
        # Save the plot
        os.makedirs('data/figures', exist_ok=True)
        fig.write_html('data/figures/weekly_distance.html')
    
    def plot_heartrate_zones(self, activity_type=None):
        """Plot heart rate zones for activities"""
        # Removed as requested
        pass
    
    def training_load_analysis(self, activity_type=None):
        """Analyze training load using moving time and heart rate"""
        if self.df is None:
            return
        
        df = self.filter_activity_type(activity_type) if activity_type else self.df
        
        if df is None or len(df) == 0:
            return
        
        # Calculate a simple training load score (moving time * average heart rate)
        if 'average_heartrate' in df.columns and 'moving_time' in df.columns:
            df['training_load'] = df['moving_time'] * df['average_heartrate'] / 3600  # Normalize by hour
            
            # Resample by day
            df = df.set_index('start_date_local')
            daily_load = df['training_load'].resample('D').sum()
            
            # Calculate 7-day rolling average
            rolling_load = daily_load.rolling(window=7).mean()
            
            # Create the plot
            fig = go.Figure()
            
            # Add daily load bars
            fig.add_trace(go.Bar(
                x=daily_load.index,
                y=daily_load.values,
                name='Daily Load',
                opacity=0.6
            ))
            
            # Add 7-day average line
            fig.add_trace(go.Scatter(
                x=rolling_load.index,
                y=rolling_load.values,
                name='7-Day Average',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title='Training Load',
                xaxis_title='Date',
                yaxis_title='Training Load',
                template='plotly_dark',
                height=600,
                width=1000
            )
            
            # Save the plot
            os.makedirs('data/figures', exist_ok=True)
            fig.write_html('data/figures/training_load.html')