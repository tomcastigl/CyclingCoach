import os
import pandas as pd
import numpy as np
import requests
from src.strava_api import StravaAPI
import json
from datetime import datetime
import argparse
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set default theme for all plots
px.defaults.template = "plotly_dark"

# Add a custom JSON encoder class to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class DetailedActivityAnalyzer:
    def __init__(self):
        """Initialize the analyzer with Strava API"""
        self.strava = StravaAPI()
        
        # Create data directories if they don't exist
        os.makedirs('data/detailed', exist_ok=True)
        os.makedirs('data/streams', exist_ok=True)
        os.makedirs('data/figures/detailed', exist_ok=True)
    
    def get_activities(self, days=7, activity_type=None):
        """Get activities summary dataframe"""
        # First, check if we have cached activities
        csv_path = 'data/activities.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if 'start_date_local' in df.columns:
                df['start_date_local'] = pd.to_datetime(df['start_date_local'])
            
            # Filter by date if specified
            if days:
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
                
                # Handle timezone-aware datetime comparison
                if 'start_date_local' in df.columns:
                    # Convert to pandas Timestamp for consistent handling
                    cutoff_date_ts = cutoff_date
                    
                    # Check if start_date_local column has timezone info
                    if hasattr(df['start_date_local'].dtype, 'tz') and df['start_date_local'].dtype.tz is not None:
                        # Convert cutoff_date to timezone-aware
                        cutoff_date_ts = cutoff_date_ts.tz_localize('UTC')
                    
                    # Filter data
                    df = df[df['start_date_local'] >= cutoff_date_ts]
            
            # Filter by activity type if specified
            if activity_type:
                df = df[df['type'] == activity_type]
            
            return df
        else:
            # Fetch activities from Strava API
            activities = self.strava.get_activities(days=days)
            if activities:
                df = self.strava.parse_activities(activities)
                
                # Filter by activity type if specified
                if activity_type and df is not None:
                    df = df[df['type'] == activity_type]
                
                return df
            return None
    
    def get_detailed_activity(self, activity_id):
        """Get detailed information for a specific activity"""
        activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {'Authorization': f'Bearer {self.strava.access_token}'}
        params = {'include_all_efforts': True}
        
        try:
            response = requests.get(activity_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return None
            
            return response.json()
        except Exception as e:
            print(f"Error getting detailed activity: {e}")
            return None
    
    def get_activity_streams(self, activity_id):
        """Get detailed data streams for a specific activity"""
        # First check if we have cached streams
        stream_path = f'data/streams/{activity_id}.json'
        if os.path.exists(stream_path):
            with open(stream_path, 'r') as f:
                return json.load(f)
        
        # If not cached, fetch from API
        streams = self.strava.get_activity_streams(activity_id)
        
        # Cache the streams for future use
        if streams:
            with open(stream_path, 'w') as f:
                json.dump(streams, f)
        
        return streams
    
    def process_activity_data(self, activity_id):
        """Process detailed activity data and streams"""
        # Get detailed activity data
        activity_data = self.get_detailed_activity(activity_id)
        if not activity_data:
            return None
        
        # Get activity streams
        streams = self.get_activity_streams(activity_id)
        if not streams:
            print(f"No streams found for activity {activity_id}")
            return activity_data
        
        # Save detailed activity data
        detailed_path = f'data/detailed/{activity_id}.json'
        with open(detailed_path, 'w') as f:
            json.dump(activity_data, f)
        
        # Process the streams into a DataFrame
        stream_data = {}
        
        # Extract stream data for each type
        for stream_type, data in streams.items():
            if 'data' in data:
                stream_data[stream_type] = data['data']
        
        # Create DataFrame from stream data
        df = None
        if 'time' in stream_data:
            df = pd.DataFrame({'time': stream_data['time']})
            
            # Add all other streams
            for stream_type, data in stream_data.items():
                if stream_type != 'time':
                    if stream_type == 'latlng' and len(data) > 0 and isinstance(data[0], list) and len(data[0]) == 2:
                        # Special handling for latlng which is a list of [lat, lng] pairs
                        df['latitude'] = [coord[0] for coord in data]
                        df['longitude'] = [coord[1] for coord in data]
                    else:
                        df[stream_type] = data
        
        # Add activity name and ID for reference
        if df is not None:
            df['activity_id'] = activity_id
            df['activity_name'] = activity_data.get('name')
            
            # Save stream DataFrame to CSV
            csv_path = f'data/streams/{activity_id}.csv'
            df.to_csv(csv_path, index=False)
            print(f"Saved detailed stream data to {csv_path}")
        
        return activity_data, df
    
    def analyze_streams(self, df, activity_data):
        """Analyze stream data for insights"""
        if df is None:
            return None
        
        # Basic analysis
        analysis = {}
        
        # Time in heart rate zones
        if 'heartrate' in df.columns:
            # Define heart rate zones (approximate, should be customized per athlete)
            max_hr = activity_data.get('max_heartrate', df['heartrate'].max())
            
            # Calculate heart rate zones based on max HR
            zones = {
                'Z1': (0, int(max_hr * 0.6)),
                'Z2': (int(max_hr * 0.6), int(max_hr * 0.7)),
                'Z3': (int(max_hr * 0.7), int(max_hr * 0.8)),
                'Z4': (int(max_hr * 0.8), int(max_hr * 0.9)),
                'Z5': (int(max_hr * 0.9), int(max_hr * 1.1))
            }
            
            # Calculate time spent in each zone
            hr_zones = {}
            for zone, (lower, upper) in zones.items():
                zone_data = df[(df['heartrate'] >= lower) & (df['heartrate'] < upper)]
                if len(zone_data) > 0 and 'time' in zone_data.columns:
                    # Calculate time spent in seconds
                    if len(zone_data) > 1:
                        time_in_zone = zone_data['time'].iloc[-1] - zone_data['time'].iloc[0]
                    else:
                        time_in_zone = 0
                    
                    hr_zones[zone] = {
                        'time_seconds': time_in_zone,
                        'percentage': time_in_zone / df['time'].iloc[-1] * 100 if df['time'].iloc[-1] > 0 else 0
                    }
            
            analysis['heart_rate_zones'] = hr_zones
        
        # Power analysis (if available)
        if 'watts' in df.columns and not df['watts'].isna().all():
            # Clean and filter power data
            power_data = df[df['watts'] > 0]['watts']
            
            if len(power_data) > 0:
                # Calculate power metrics
                analysis['power'] = {
                    'average': power_data.mean(),
                    'max': power_data.max(),
                    'normalized_power': self.calculate_normalized_power(power_data),
                    # Calculate power zones based on FTP
                    # FTP could be provided as input or estimated
                    'ftp_estimate': self.estimate_ftp(power_data)
                }
                
                # Calculate power curve (best power for different durations)
                analysis['power_curve'] = self.calculate_power_curve(power_data)
        
        # Cadence analysis
        if 'cadence' in df.columns and not df['cadence'].isna().all():
            cadence_data = df[df['cadence'] > 0]['cadence']
            
            if len(cadence_data) > 0:
                analysis['cadence'] = {
                    'average': cadence_data.mean(),
                    'max': cadence_data.max(),
                    'distribution': self.calculate_distribution(cadence_data, bin_size=5)
                }
        
        # Elevation analysis
        if 'altitude' in df.columns:
            altitude_data = df['altitude']
            if not altitude_data.isna().all():
                # Calculate elevation gain/loss
                altitude_diff = altitude_data.diff().fillna(0)
                elevation_gain = altitude_diff[altitude_diff > 0].sum()
                elevation_loss = abs(altitude_diff[altitude_diff < 0].sum())
                
                analysis['elevation'] = {
                    'gain': elevation_gain,
                    'loss': elevation_loss,
                    'max': altitude_data.max(),
                    'min': altitude_data.min()
                }
                
                # Calculate gradient distribution if grade_smooth available
                if 'grade_smooth' in df.columns:
                    grade_data = df['grade_smooth']
                    analysis['elevation']['gradient_distribution'] = self.calculate_distribution(grade_data, bin_size=1)
        
        # Speed analysis
        if 'velocity_smooth' in df.columns:
            speed_data = df['velocity_smooth']
            
            if not speed_data.isna().all():
                analysis['speed'] = {
                    'average': speed_data.mean(),
                    'max': speed_data.max(),
                    'distribution': self.calculate_distribution(speed_data, bin_size=1)
                }
        
        return analysis
    
    def calculate_normalized_power(self, power_series):
        """Calculate normalized power from power data"""
        if len(power_series) < 30:
            return None
        
        # Convert to numpy array for faster computation
        power_array = power_series.to_numpy()
        
        # Calculate 30-second moving average
        window_size = 30  # assuming data points are 1 second apart
        weights = np.ones(window_size) / window_size
        power_30s = np.convolve(power_array, weights, 'valid')
        
        # Raise to 4th power
        power_30s_4 = np.power(power_30s, 4)
        
        # Average and take 4th root
        if len(power_30s_4) > 0:
            return np.power(np.mean(power_30s_4), 0.25)
        else:
            return None
    
    def estimate_ftp(self, power_series):
        """Estimate FTP from power data (simple method: 95% of 20-min max power)"""
        if len(power_series) < 1200:  # at least 20 minutes of data (assuming 1s intervals)
            return None
        
        # Convert to numpy array
        power_array = power_series.to_numpy()
        
        # Calculate 20-minute moving average
        window_size = 1200  # 20 minutes at 1 second intervals
        weights = np.ones(window_size) / window_size
        power_20min = np.convolve(power_array, weights, 'valid')
        
        # Find max 20-minute power
        if len(power_20min) > 0:
            max_20min_power = np.max(power_20min)
            # FTP is approximately 95% of 20-minute power
            return max_20min_power * 0.95
        else:
            return None
    
    def calculate_power_curve(self, power_series):
        """Calculate power curve (max power for different durations)"""
        if len(power_series) < 60:
            return {}
        
        # Define durations to calculate (in seconds)
        durations = [5, 10, 30, 60, 300, 600, 1200, 1800, 3600]
        power_curve = {}
        
        # Convert to numpy array
        power_array = power_series.to_numpy()
        
        for duration in durations:
            if len(power_array) < duration:
                continue
                
            # Calculate moving average for the duration
            weights = np.ones(duration) / duration
            moving_avg = np.convolve(power_array, weights, 'valid')
            
            if len(moving_avg) > 0:
                power_curve[f"{duration}s"] = float(np.max(moving_avg))
        
        return power_curve
    
    def calculate_distribution(self, series, bin_size=1):
        """Calculate distribution of values in bins"""
        if len(series) == 0:
            return {}
            
        # Define bins
        min_val = int(series.min())
        max_val = int(series.max()) + 1
        bins = range(min_val, max_val, bin_size)
        
        # Count values in each bin
        hist, edges = np.histogram(series, bins=bins)
        
        # Convert to dictionary
        distribution = {}
        for i in range(len(hist)):
            bin_range = f"{edges[i]:.1f}-{edges[i+1]:.1f}"
            distribution[bin_range] = int(hist[i])
        
        return distribution
    
    def generate_activity_visualizations(self, activity_id, activity_name, df):
        """Generate all visualizations for a single activity"""
        # Create filesystem-friendly activity name
        safe_name = activity_name.replace(' ', '_')
        
        # Get activity data to get start time
        activity_data = self.get_detailed_activity(activity_id)
        if activity_data and 'start_date_local' in activity_data:
            start_time = pd.to_datetime(activity_data['start_date_local'])
            datetime_str = start_time.strftime('%Y%m%d_%H%M%S')
        else:
            # Fallback to current time if we can't get activity data
            datetime_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create subfolder for this activity using activity name and datetime
        folder_name = f'{safe_name}_{datetime_str}'
        os.makedirs(f'data/figures/detailed/{folder_name}', exist_ok=True)
        
        # Create dashboard
        self.create_activity_dashboard(df, activity_id, activity_name, folder_name)
        
        # Create enhanced map
        self.create_enhanced_map(df, activity_id, 'altitude', 'Altitude (m)', 'earth', folder_name=folder_name)
        
        print(f"Visualizations for activity '{activity_name}' saved to data/figures/detailed/{folder_name}/")
    
    def create_activity_dashboard(self, df, activity_id, activity_name, folder_name):
        """Create a consolidated dashboard with all visualizations for an activity"""
        # Determine what data is available
        has_hr = 'heartrate' in df.columns and not df['heartrate'].isna().all()
        has_power = 'watts' in df.columns and not df['watts'].isna().all()
        has_speed = 'velocity_smooth' in df.columns and not df['velocity_smooth'].isna().all()
        has_cadence = 'cadence' in df.columns and not df['cadence'].isna().all()
        has_altitude = 'altitude' in df.columns and not df['altitude'].isna().all()
        has_map = 'latitude' in df.columns and 'longitude' in df.columns
        
        # Create a figure with appropriate number of subplots
        fig = make_subplots(
            rows=3, 
            cols=2,
            subplot_titles=(
                "Heart Rate & Power Over Time" if has_hr or has_power else "Activity Data",
                "Speed & Cadence Over Time" if has_speed or has_cadence else "Activity Data",
                "Altitude Profile" if has_altitude else "Activity Data",
                "Route Map" if has_map else "Activity Data",
                "Heart Rate Zone Distribution" if has_hr else "Activity Data",
                "Performance Metrics"
            ),
            specs=[
                [{"type": "xy"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "mapbox" if has_map else "xy"}],
                [{"type": "pie"}, {"type": "table"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        # 1. Heart Rate & Power
        if has_hr or has_power:
            # Primary y-axis for heart rate
            if has_hr:
                fig.add_trace(
                    go.Scatter(
                        x=df['time']/60, 
                        y=df['heartrate'],
                        name="Heart Rate",
                        line=dict(color="#e74c3c", width=2)
                    ),
                    row=1, col=1
                )
            
            # Secondary y-axis for power
            if has_power:
                fig.add_trace(
                    go.Scatter(
                        x=df['time']/60, 
                        y=df['watts'],
                        name="Power",
                        line=dict(color="#2ecc71", width=2),
                        yaxis="y2"
                    ),
                    row=1, col=1
                )
                
                # Add secondary y-axis
                fig.update_layout(
                    yaxis2=dict(
                        title="Power (watts)",
                        titlefont=dict(color="#2ecc71"),
                        tickfont=dict(color="#2ecc71"),
                        anchor="x",
                        overlaying="y",
                        side="right"
                    )
                )
            
            # Update layout for this subplot
            fig.update_xaxes(title_text="Time (minutes)", row=1, col=1)
            fig.update_yaxes(title_text="Heart Rate (bpm)" if has_hr else "", row=1, col=1)
        
        # 2. Speed & Cadence
        if has_speed or has_cadence:
            # Primary y-axis for speed
            if has_speed:
                fig.add_trace(
                    go.Scatter(
                        x=df['time']/60, 
                        y=df['velocity_smooth']*3.6,  # Convert to km/h
                        name="Speed",
                        line=dict(color="#3498db", width=2)
                    ),
                    row=1, col=2
                )
            
            # Secondary y-axis for cadence
            if has_cadence:
                fig.add_trace(
                    go.Scatter(
                        x=df['time']/60, 
                        y=df['cadence'],
                        name="Cadence",
                        line=dict(color="#9b59b6", width=2),
                        yaxis="y3"
                    ),
                    row=1, col=2
                )
                
                # Add secondary y-axis
                fig.update_layout(
                    yaxis3=dict(
                        title="Cadence (rpm)",
                        titlefont=dict(color="#9b59b6"),
                        tickfont=dict(color="#9b59b6"),
                        anchor="x2",
                        overlaying="y3",
                        side="right"
                    )
                )
            
            # Update layout for this subplot
            fig.update_xaxes(title_text="Time (minutes)", row=1, col=2)
            fig.update_yaxes(title_text="Speed (km/h)" if has_speed else "", row=1, col=2)
        
        # 3. Altitude Profile
        if has_altitude:
            if 'distance' in df.columns:
                x_data = df['distance']/1000  # Convert to km
                x_label = "Distance (km)"
            else:
                x_data = df['time']/60  # Convert to minutes
                x_label = "Time (minutes)"
                
            fig.add_trace(
                go.Scatter(
                    x=x_data, 
                    y=df['altitude'],
                    name="Altitude",
                    line=dict(color="#f1c40f", width=2),
                    fill='tozeroy'
                ),
                row=2, col=1
            )
            
            # Update layout for this subplot
            fig.update_xaxes(title_text=x_label, row=2, col=1)
            fig.update_yaxes(title_text="Altitude (m)", row=2, col=1)
        
        # 4. Route Map
        if has_map:
            fig.add_trace(
                go.Scattermapbox(
                    lat=df['latitude'],
                    lon=df['longitude'],
                    mode='lines',
                    line=dict(width=4, color='#e74c3c'),
                    name="Route"
                ),
                row=2, col=2
            )
            
            # Calculate the center of the map
            center_lat = df['latitude'].mean()
            center_lon = df['longitude'].mean()
            
            # Update the mapbox configuration
            fig.update_layout(
                mapbox=dict(
                    style="carto-darkmatter",
                    center=dict(lat=center_lat, lon=center_lon),
                    zoom=11
                )
            )
        
        # 5. Heart Rate Zone Distribution
        if has_hr:
            # Define heart rate zones (approximate, should be customized per athlete)
            max_hr = df['heartrate'].max()
            
            # Calculate heart rate zones based on max HR
            zones = {
                'Z1 (Easy)': (0, int(max_hr * 0.6)),
                'Z2 (Endurance)': (int(max_hr * 0.6), int(max_hr * 0.7)),
                'Z3 (Tempo)': (int(max_hr * 0.7), int(max_hr * 0.8)),
                'Z4 (Threshold)': (int(max_hr * 0.8), int(max_hr * 0.9)),
                'Z5 (Max)': (int(max_hr * 0.9), int(max_hr * 1.1))
            }
            
            # Calculate time spent in each zone
            zone_data = []
            zone_labels = []
            zone_colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
            
            for i, (zone, (lower, upper)) in enumerate(zones.items()):
                zone_mask = (df['heartrate'] >= lower) & (df['heartrate'] < upper)
                if any(zone_mask):
                    # Calculate time in minutes
                    if 'time' in df.columns:
                        zone_time = zone_mask.sum() / 60  # Approximate time in minutes based on data points
                        zone_data.append(zone_time)
                        zone_labels.append(zone)
            
            # Create pie chart
            fig.add_trace(
                go.Pie(
                    labels=zone_labels,
                    values=zone_data,
                    name="HR Zones",
                    marker=dict(colors=zone_colors),
                    textinfo='percent',
                    hoverinfo='label+percent',
                    hole=0.3
                ),
                row=3, col=1
            )
        
        # 6. Performance Metrics
        metrics = []
        values = []
        
        if has_hr:
            metrics.extend(["Avg HR", "Max HR"])
            values.extend([df['heartrate'].mean(), df['heartrate'].max()])
        
        if has_power:
            metrics.extend(["Avg Power", "Max Power", "NP (est)"])
            np_est = self.calculate_normalized_power(df['watts'])
            values.extend([df['watts'].mean(), df['watts'].max(), np_est if np_est else 0])
        
        if has_speed:
            metrics.extend(["Avg Speed", "Max Speed"])
            values.extend([df['velocity_smooth'].mean() * 3.6, df['velocity_smooth'].max() * 3.6])
        
        if has_cadence:
            metrics.extend(["Avg Cadence"])
            values.extend([df[df['cadence'] > 0]['cadence'].mean()])
        
        if has_altitude:
            altitude_diff = df['altitude'].diff().fillna(0)
            elevation_gain = altitude_diff[altitude_diff > 0].sum()
            metrics.extend(["Elevation Gain"])
            values.extend([elevation_gain])
        
        # Create a table
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["Metric", "Value"],
                    fill_color='rgba(52, 73, 94, 0.8)',
                    align='left',
                    font=dict(color='white', size=14)
                ),
                cells=dict(
                    values=[metrics, [f"{v:.1f}" for v in values]],
                    fill_color='rgba(52, 73, 94, 0.5)',
                    align='left',
                    font=dict(color='white', size=12)
                )
            ),
            row=3, col=2
        )
        
        # Update overall layout
        fig.update_layout(
            title=dict(
                text=f"{activity_name} - Activity Dashboard",
                font=dict(size=24)
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            autosize=False,
            width=1200,
            height=1200,
            margin=dict(l=50, r=50, b=50, t=100),
            template="plotly_dark"
        )
        
        # Save as interactive HTML
        fig.write_html(f'data/figures/detailed/{folder_name}/dashboard.html')
        
        # Create individual plots for specific sections (optional)
        
        # 1. If we have map data with altitude or speed, create enhanced maps
        if has_map:
            if has_altitude:
                self.create_enhanced_map(df, activity_id, 'altitude', 'Altitude (m)', 'earth', folder_name=folder_name)
            
            if has_speed:
                self.create_enhanced_map(df, activity_id, 'velocity_smooth', 'Speed (km/h)', 'viridis', multiplier=3.6, folder_name=folder_name)
    
    def create_enhanced_map(self, df, activity_id, color_col, color_label, colorscale, multiplier=1.0, folder_name=None):
        """Create an enhanced map visualization with color coding"""
        if color_col in df.columns and 'latitude' in df.columns and 'longitude' in df.columns:
            try:
                # Convert to numeric and handle any non-numeric values
                data_values = pd.to_numeric(df[color_col], errors='coerce')
                # Apply multiplier only if we have valid numeric data
                if not data_values.isna().all():
                    data_values = data_values.astype(float) * float(multiplier)
                
                fig = px.scatter_mapbox(
                    df, 
                    lat='latitude', 
                    lon='longitude',
                    color=data_values,
                    color_continuous_scale=colorscale,
                    zoom=11,
                    mapbox_style="carto-darkmatter",
                    title=f"Route Map - Color by {color_label}"
                )
                
                fig.update_layout(
                    coloraxis_colorbar=dict(title=color_label),
                    height=800,
                    width=800
                )
                
                # Save as interactive HTML
                if folder_name:
                    fig.write_html(f'data/figures/detailed/{folder_name}/map_{color_col}.html')
                else:
                    fig.write_html(f'data/figures/detailed/{activity_id}/map_{color_col}.html')
            except Exception as e:
                print(f"Warning: Could not create enhanced map for {color_col}: {str(e)}")