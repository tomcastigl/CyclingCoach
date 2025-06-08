import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    def plot_weekly_distance(self, activity_type='Ride'):
        """Plot weekly distance for a specific activity type"""
        if self.df is None or len(self.df) == 0:
            print("No activities available for plotting")
            return
        
        # Filter by activity type
        df = self.filter_activity_type(activity_type)
        
        if df is None or len(df) == 0:
            print(f"No {activity_type} activities found")
            return
        
        # Resample by week and calculate total distance
        df = df.set_index('start_date_local')
        weekly_distance = df['distance'].resample('W').sum() / 1000  # Convert to km
        
        # Reset index to make date a column for plotting
        weekly_distance = weekly_distance.reset_index()
        weekly_distance.columns = ['Week', 'Distance (km)']
        
        # Create the plot
        fig = px.bar(
            weekly_distance, 
            x='Week', 
            y='Distance (km)',
            title=f'Weekly {activity_type} Distance',
            labels={'Week': 'Week', 'Distance (km)': 'Distance (km)'},
            color_discrete_sequence=['#36A2EB']
        )
        
        fig.update_layout(
            title_font_size=24,
            xaxis_title_font_size=18,
            yaxis_title_font_size=18,
            legend_title_font_size=18,
            legend_font_size=15,
            height=600,
            width=1000
        )
        
        # Save figure
        os.makedirs('data/figures', exist_ok=True)
        fig.write_html(f'data/figures/weekly_{activity_type.lower()}_distance.html')
        fig.write_image(f'data/figures/weekly_{activity_type.lower()}_distance.png')
        
        print(f"Weekly {activity_type} distance plot saved to data/figures/weekly_{activity_type.lower()}_distance.png")
    
    def plot_heartrate_zones(self, activity_type='Ride'):
        """Plot time spent in heart rate zones"""
        if self.df is None or len(self.df) == 0:
            print("No activities available for plotting")
            return
        
        # Filter by activity type
        df = self.filter_activity_type(activity_type)
        
        if df is None or len(df) == 0 or 'average_heartrate' not in df.columns:
            print(f"No {activity_type} activities with heart rate data found")
            return
        
        # Define heart rate zones (approximate, should be customized per athlete)
        zone_boundaries = [0, 120, 140, 160, 180, 200]
        zone_names = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
        
        # Create heart rate zone column
        df['hr_zone'] = pd.cut(
            df['average_heartrate'], 
            bins=zone_boundaries, 
            labels=zone_names,
            right=False
        )
        
        # Calculate time spent in each zone
        zone_time = df.groupby('hr_zone')['moving_time'].sum() / 60  # Convert to minutes
        zone_time = zone_time.reset_index()
        zone_time.columns = ['Heart Rate Zone', 'Time (minutes)']
        
        # Create color map for zones
        colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
        
        # Create the plot
        fig = px.bar(
            zone_time, 
            x='Heart Rate Zone', 
            y='Time (minutes)',
            title=f'Time Spent in Heart Rate Zones ({activity_type})',
            labels={'Heart Rate Zone': 'Heart Rate Zone', 'Time (minutes)': 'Time (minutes)'},
            color='Heart Rate Zone',
            color_discrete_map={zone: color for zone, color in zip(zone_names, colors)}
        )
        
        fig.update_layout(
            title_font_size=24,
            xaxis_title_font_size=18,
            yaxis_title_font_size=18,
            legend_title_font_size=18,
            legend_font_size=15,
            height=600,
            width=1000
        )
        
        # Save figure
        os.makedirs('data/figures', exist_ok=True)
        fig.write_html(f'data/figures/{activity_type.lower()}_hr_zones.html')
        fig.write_image(f'data/figures/{activity_type.lower()}_hr_zones.png')
        
        print(f"{activity_type} heart rate zones plot saved to data/figures/{activity_type.lower()}_hr_zones.png")
    
    def training_load_analysis(self, activity_type='Ride'):
        """Analyze training load using moving time and heart rate"""
        if self.df is None or len(self.df) == 0:
            print("No activities available for analysis")
            return
        
        # Filter by activity type
        df = self.filter_activity_type(activity_type)
        
        if df is None or len(df) == 0:
            print(f"No {activity_type} activities found")
            return
        
        # Calculate a simple training load score (moving time * average heart rate)
        if 'average_heartrate' in df.columns and 'moving_time' in df.columns:
            df['training_load'] = df['moving_time'] * df['average_heartrate'] / 3600  # Normalize by hour
            
            # Resample by day
            df = df.set_index('start_date_local')
            daily_load = df['training_load'].resample('D').sum()
            
            # Calculate 7-day rolling average
            rolling_load = daily_load.rolling(window=7).mean()
            
            # Prepare data for plotting
            daily_load_df = daily_load.reset_index()
            daily_load_df.columns = ['Date', 'Daily Load']
            
            rolling_load_df = rolling_load.reset_index()
            rolling_load_df.columns = ['Date', '7-Day Average']
            
            # Create the plot
            fig = make_subplots(specs=[[{"secondary_y": False}]])
            
            # Add daily load bars
            fig.add_trace(
                go.Bar(
                    x=daily_load_df['Date'],
                    y=daily_load_df['Daily Load'],
                    name='Daily Load',
                    marker_color='#3498db'
                )
            )
            
            # Add 7-day average line
            fig.add_trace(
                go.Scatter(
                    x=rolling_load_df['Date'],
                    y=rolling_load_df['7-Day Average'],
                    name='7-Day Average',
                    line=dict(color='#e74c3c', width=3)
                )
            )
            
            # Update layout
            fig.update_layout(
                title=f'{activity_type} Training Load',
                title_font_size=24,
                xaxis_title='Date',
                xaxis_title_font_size=18,
                yaxis_title='Training Load',
                yaxis_title_font_size=18,
                legend_title_font_size=18,
                legend_font_size=15,
                height=600,
                width=1000,
                template="plotly_dark"
            )
            
            # Save figure
            os.makedirs('data/figures', exist_ok=True)
            fig.write_html(f'data/figures/{activity_type.lower()}_training_load.html')
            fig.write_image(f'data/figures/{activity_type.lower()}_training_load.png')
            
            print(f"{activity_type} training load plot saved to data/figures/{activity_type.lower()}_training_load.png")
        else:
            print("Heart rate or moving time data not available for training load analysis")

def main():
    # Initialize analyzer
    analyzer = ActivityAnalyzer()
    
    if analyzer.df is not None:
        # Print summary statistics
        stats = analyzer.summary_stats()
        if stats:
            print("\nActivity Summary:")
            for key, value in stats.items():
                print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        
        # Generate plots
        analyzer.plot_weekly_distance()
        analyzer.plot_heartrate_zones()
        analyzer.training_load_analysis()

if __name__ == "__main__":
    main() 