"""
OpenAI Integration Module for CyclingCoach.

This module handles formatting cycling data in an LLM-friendly format
and sending requests to OpenAI for analysis.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import openai
from dotenv import dotenv_values
import glob
from pathlib import Path
import base64
from PIL import Image
import io
import tempfile
import subprocess
import time
import shutil

class OpenAICoach:
    def __init__(self, config_path='config/.env'):
        """Initialize the OpenAI coach with API credentials"""
        # Load environment variables from .env file
        env_vars = dotenv_values(config_path)
        self.api_key = env_vars.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found in config/.env")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Set default model
        self.model = "gpt-4o"
    
    def format_activity_data(self, activity_id=None, days=7, activity_type='Ride', 
                             include_timeseries=True, sample_rate=30, max_points=500,
                             timeseries_fields=None, use_visualizations=True, include_images=False,
                             max_images=3, convert_html=True):
        """Format activity data in an LLM-friendly format
        
        Args:
            activity_id: Specific activity ID to analyze
            days: Number of days to analyze
            activity_type: Type of activity to analyze
            include_timeseries: Whether to include full timeseries data
            sample_rate: Sample rate for timeseries data (every N points)
            max_points: Maximum number of data points to include per activity
            timeseries_fields: List of specific timeseries fields to include (None for all)
            use_visualizations: Whether to use dashboard visualizations instead of raw data
            include_images: Whether to include base64-encoded images of visualizations
            max_images: Maximum number of images per activity
            convert_html: Whether to convert HTML dashboards to images
        """
        # Load activities summary
        activities_path = 'data/activities.csv'
        if not os.path.exists(activities_path):
            raise FileNotFoundError(f"Activities file not found: {activities_path}")
        
        activities_df = pd.read_csv(activities_path)
        
        # Check if we have any activities
        if len(activities_df) == 0:
            return None
            
        activities_df['start_date_local'] = pd.to_datetime(activities_df['start_date_local'])
        
        # Filter by date
        if days:
            try:
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
                
                # Check if start_date_local has timezone info and handle accordingly
                if hasattr(activities_df['start_date_local'].dtype, 'tz') and activities_df['start_date_local'].dtype.tz is not None:
                    # If activities have timezone, localize cutoff_date to match
                    cutoff_date = cutoff_date.tz_localize(activities_df['start_date_local'].dtype.tz)
                elif len(activities_df) > 0 and hasattr(activities_df['start_date_local'].iloc[0], 'tz') and activities_df['start_date_local'].iloc[0].tz is not None:
                    # Handle case where individual timestamps have timezone
                    cutoff_date = cutoff_date.tz_localize(activities_df['start_date_local'].iloc[0].tz)
                
                activities_df = activities_df[activities_df['start_date_local'] >= cutoff_date]
            except Exception as e:
                print(f"Warning: Error filtering by date: {e}")
                # Alternative approach: convert all to naive datetimes
                try:
                    cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).tz_localize(None)
                    activities_df['start_date_local'] = activities_df['start_date_local'].dt.tz_localize(None)
                    activities_df = activities_df[activities_df['start_date_local'] >= cutoff_date]
                except Exception as e2:
                    print(f"Warning: Could not filter by date: {e2}")
                    # Last resort: don't filter by date
                    pass
        
        # Filter by activity type
        if activity_type:
            activities_df = activities_df[activities_df['type'] == activity_type]
        
        # Filter by activity ID if specified
        if activity_id:
            try:
                activity_id_int = int(activity_id)
                activities_df = activities_df[activities_df['id'] == activity_id_int]
            except (ValueError, TypeError):
                print(f"Warning: Invalid activity ID: {activity_id}")
        
        if len(activities_df) == 0:
            return None
        
        # Default timeseries fields if not specified
        if timeseries_fields is None:
            timeseries_fields = ['time', 'distance', 'heartrate', 'altitude', 'velocity_smooth', 'grade_smooth']
        
        # Format activities data
        activities_data = []
        for _, activity in activities_df.iterrows():
            try:
                activity_id = str(int(activity['id']))
                
                # Load detailed analysis if available
                analysis_path = f'data/detailed/{activity_id}_analysis.json'
                detailed_data = {}
                if os.path.exists(analysis_path):
                    try:
                        with open(analysis_path, 'r') as f:
                            detailed_data = json.load(f)
                        print(f"Loaded detailed analysis for activity {activity_id}")
                    except Exception as e:
                        print(f"Error loading detailed analysis for activity {activity_id}: {e}")
                
                # Format basic activity data
                activity_data = {
                    'id': activity_id,
                    'name': activity['name'],
                    'date': activity['start_date_local'].strftime('%Y-%m-%d %H:%M'),
                    'distance_km': round(float(activity['distance']) / 1000, 2),
                    'moving_time_min': round(float(activity['moving_time']) / 60, 2),
                    'elevation_gain_m': float(activity['total_elevation_gain']),
                    'average_speed_kmh': round(float(activity['average_speed']) * 3.6, 2),
                    'max_speed_kmh': round(float(activity['max_speed']) * 3.6, 2),
                }
                
                # Add heart rate data if available
                if 'average_heartrate' in activity and not pd.isna(activity['average_heartrate']):
                    activity_data['average_heartrate'] = float(activity['average_heartrate'])
                if 'max_heartrate' in activity and not pd.isna(activity['max_heartrate']):
                    activity_data['max_heartrate'] = float(activity['max_heartrate'])
                
                # Add power data if available
                if 'average_watts' in activity and not pd.isna(activity['average_watts']):
                    activity_data['average_watts'] = float(activity['average_watts'])
                if 'max_watts' in activity and not pd.isna(activity['max_watts']):
                    activity_data['max_watts'] = float(activity['max_watts'])
                if 'weighted_average_watts' in activity and not pd.isna(activity['weighted_average_watts']):
                    activity_data['normalized_power'] = float(activity['weighted_average_watts'])
                
                # Add detailed analysis data if available
                if detailed_data:
                    # Heart rate zones
                    if 'heart_rate_zones' in detailed_data:
                        activity_data['heart_rate_zones'] = detailed_data['heart_rate_zones']
                    elif 'hr_zones' in detailed_data:
                        activity_data['heart_rate_zones'] = detailed_data['hr_zones']
                    
                    # Power zones
                    if 'power_zones' in detailed_data:
                        activity_data['power_zones'] = detailed_data['power_zones']
                    
                    # Climbs
                    if 'climbs' in detailed_data:
                        activity_data['climbs'] = detailed_data['climbs']
                    
                    # Elevation data
                    if 'elevation' in detailed_data:
                        activity_data['elevation'] = detailed_data['elevation']
                    
                    # Speed data
                    if 'speed' in detailed_data:
                        activity_data['speed'] = detailed_data['speed']
                    
                    # Intervals
                    if 'intervals' in detailed_data:
                        activity_data['intervals'] = detailed_data['intervals']
                
                # Add dashboard visualizations if requested
                if use_visualizations:
                    # Look for dashboard files
                    dashboard_paths = self._find_dashboard_files(activity_id, activity['name'])
                    if dashboard_paths:
                        activity_data['visualizations'] = dashboard_paths
                        print(f"Found {len(dashboard_paths)} visualizations for activity {activity_id}")
                        
                        # Add images if requested
                        if include_images:
                            encoded_images = []
                            
                            # First try to find existing image files
                            image_paths = self._find_image_files(activity_id, activity['name'])
                            
                            # If no images found or we want to convert HTML to images
                            if (not image_paths or convert_html) and dashboard_paths:
                                # Convert HTML dashboards to images
                                html_image_paths = self._convert_html_to_images(dashboard_paths, max_count=max_images)
                                if html_image_paths:
                                    # Add any existing image paths
                                    if image_paths:
                                        all_image_paths = image_paths + html_image_paths
                                    else:
                                        all_image_paths = html_image_paths
                                    
                                    # Limit number of images
                                    image_paths = all_image_paths[:max_images]
                            else:
                                # Limit number of images
                                image_paths = image_paths[:max_images]
                            
                            # Encode images as base64
                            if image_paths:
                                for img_path in image_paths:
                                    try:
                                        with open(img_path, 'rb') as img_file:
                                            encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
                                            encoded_images.append({
                                                'path': img_path,
                                                'data': encoded_img
                                            })
                                    except Exception as e:
                                        print(f"Error encoding image {img_path}: {e}")
                                
                                if encoded_images:
                                    activity_data['images'] = encoded_images
                                    print(f"Added {len(encoded_images)} encoded images for activity {activity_id}")
                
                # Add timeseries data if requested and no visualizations were found
                if include_timeseries and (not use_visualizations or 'visualizations' not in activity_data):
                    streams_path = f'data/streams/{activity_id}.csv'
                    if os.path.exists(streams_path):
                        try:
                            streams_df = pd.read_csv(streams_path)
                            
                            # Filter to only include requested fields
                            available_fields = [col for col in timeseries_fields if col in streams_df.columns]
                            streams_df = streams_df[['time'] + [f for f in available_fields if f != 'time']]
                            
                            # Calculate appropriate sample rate based on max_points
                            if max_points and len(streams_df) > max_points:
                                actual_sample_rate = max(sample_rate, len(streams_df) // max_points)
                            else:
                                actual_sample_rate = sample_rate
                            
                            # Sample the data to reduce size
                            if actual_sample_rate > 1:
                                streams_df = streams_df.iloc[::actual_sample_rate].reset_index(drop=True)
                            
                            # Convert to dictionary format
                            timeseries = {}
                            for column in streams_df.columns:
                                if column not in ['activity_id', 'activity_name']:
                                    # Handle NaN values
                                    if streams_df[column].dtype == 'float64':
                                        timeseries[column] = streams_df[column].fillna(0).tolist()
                                    else:
                                        timeseries[column] = streams_df[column].fillna('').tolist()
                            
                            activity_data['timeseries'] = timeseries
                            print(f"Added timeseries data for activity {activity_id} (sampled at 1:{actual_sample_rate}, {len(streams_df)} points)")
                        except Exception as e:
                            print(f"Error loading timeseries data for activity {activity_id}: {e}")
                
                activities_data.append(activity_data)
            except Exception as e:
                print(f"Warning: Error processing activity {activity.get('id', 'unknown')}: {e}")
                continue
        
        return activities_data
    
    def _find_dashboard_files(self, activity_id, activity_name):
        """Find dashboard files for an activity"""
        # Clean activity name for file path
        clean_name = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in activity_name)
        
        # Look in data/figures/detailed
        dashboard_dir = 'data/figures/detailed'
        dashboard_paths = set()  # Use a set to avoid duplicates
        
        # First, look for exact ID match in directory name
        exact_match_dirs = []
        for root, dirs, files in os.walk(dashboard_dir):
            for dir_name in dirs:
                if activity_id in dir_name:
                    exact_match_dirs.append(os.path.join(root, dir_name))
        
        # If we found exact ID matches, prioritize those
        if exact_match_dirs:
            for dir_path in exact_match_dirs:
                for file in os.listdir(dir_path):
                    if file.endswith('.html'):
                        dashboard_paths.add(os.path.join(dir_path, file))
        else:
            # Otherwise look for name matches
            for root, dirs, files in os.walk(dashboard_dir):
                # Check if the current directory contains the activity name
                if clean_name in os.path.basename(root):
                    # Look for HTML files directly in this directory
                    for file in files:
                        if file.endswith('.html'):
                            dashboard_paths.add(os.path.join(root, file))
                
                # Also check subdirectories
                for dir_name in dirs:
                    # Check if directory name contains activity name
                    if clean_name in dir_name:
                        dir_path = os.path.join(root, dir_name)
                        # Look for HTML files in this directory
                        if os.path.isdir(dir_path):
                            for file in os.listdir(dir_path):
                                if file.endswith('.html'):
                                    dashboard_paths.add(os.path.join(dir_path, file))
        
        # If no dashboards found, look for any HTML files in figures directory
        if not dashboard_paths:
            figures_dir = 'data/figures'
            for root, dirs, files in os.walk(figures_dir):
                for file in files:
                    if file.endswith('.html') and (activity_id in file or clean_name in file):
                        dashboard_paths.add(os.path.join(root, file))
        
        return list(dashboard_paths)
    
    def _find_image_files(self, activity_id, activity_name):
        """Find image files for an activity"""
        # Clean activity name for file path
        clean_name = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in activity_name)
        
        # Look in data/figures/detailed and data/figures
        image_paths = set()  # Use a set to avoid duplicates
        
        # First, look for exact ID match in directory name
        exact_match_dirs = []
        search_dirs = ['data/figures/detailed', 'data/figures']
        
        for figures_dir in search_dirs:
            for root, dirs, files in os.walk(figures_dir):
                for dir_name in dirs:
                    if activity_id in dir_name:
                        exact_match_dirs.append(os.path.join(root, dir_name))
        
        # If we found exact ID matches, prioritize those
        if exact_match_dirs:
            for dir_path in exact_match_dirs:
                for file in os.listdir(dir_path):
                    if file.endswith(('.png', '.jpg', '.jpeg')):
                        image_paths.add(os.path.join(dir_path, file))
        else:
            # Otherwise look for name matches
            for figures_dir in search_dirs:
                for root, dirs, files in os.walk(figures_dir):
                    # Check if the current directory contains the activity name
                    if clean_name in os.path.basename(root):
                        # Look for image files directly in this directory
                        for file in files:
                            if file.endswith(('.png', '.jpg', '.jpeg')):
                                image_paths.add(os.path.join(root, file))
                    
                    # Also check subdirectories
                    for dir_name in dirs:
                        # Check if directory name contains activity name
                        if clean_name in dir_name:
                            dir_path = os.path.join(root, dir_name)
                            # Look for image files in this directory
                            if os.path.isdir(dir_path):
                                for file in os.listdir(dir_path):
                                    if file.endswith(('.png', '.jpg', '.jpeg')):
                                        image_paths.add(os.path.join(dir_path, file))
        
        # If no images found yet, look for any image files that might contain the activity ID in the filename
        if not image_paths:
            for figures_dir in search_dirs:
                for root, dirs, files in os.walk(figures_dir):
                    for file in files:
                        if file.endswith(('.png', '.jpg', '.jpeg')) and (activity_id in file or clean_name in file):
                            image_paths.add(os.path.join(root, file))
        
        return list(image_paths)
    
    def _convert_html_to_images(self, html_paths, max_count=3):
        """Convert HTML dashboards to images using headless browser
        
        This requires either wkhtmltopdf or Chrome/Chromium with headless mode.
        """
        image_paths = []
        
        # Create temp directory for images
        temp_dir = os.path.join('data', 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Limit to max_count
        html_paths = html_paths[:max_count]
        
        try:
            # Check if wkhtmltoimage is available
            try:
                subprocess.run(['which', 'wkhtmltoimage'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                has_wkhtmltoimage = True
            except (subprocess.SubprocessError, FileNotFoundError):
                has_wkhtmltoimage = False
            
            # Check if Chrome/Chromium is available
            try:
                subprocess.run(['which', 'google-chrome'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                chrome_path = 'google-chrome'
                has_chrome = True
            except (subprocess.SubprocessError, FileNotFoundError):
                try:
                    subprocess.run(['which', 'chromium-browser'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    chrome_path = 'chromium-browser'
                    has_chrome = True
                except (subprocess.SubprocessError, FileNotFoundError):
                    try:
                        # On macOS, check for Chrome in the Applications folder
                        if os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
                            chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                            has_chrome = True
                        else:
                            has_chrome = False
                    except:
                        has_chrome = False
            
            # Convert HTML files to images
            for i, html_path in enumerate(html_paths):
                if i >= max_count:
                    break
                
                # Generate output path
                output_path = os.path.join(temp_dir, f"dashboard_{i}.png")
                
                # Try to convert using available tools
                if has_wkhtmltoimage:
                    try:
                        # Use wkhtmltoimage
                        cmd = ['wkhtmltoimage', '--quality', '80', '--width', '1200', html_path, output_path]
                        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        image_paths.append(output_path)
                        print(f"Converted {html_path} to image using wkhtmltoimage")
                    except subprocess.SubprocessError as e:
                        print(f"Error converting {html_path} with wkhtmltoimage: {e}")
                elif has_chrome:
                    try:
                        # Use Chrome/Chromium in headless mode
                        cmd = [
                            chrome_path,
                            '--headless',
                            '--disable-gpu',
                            '--screenshot=' + output_path,
                            '--window-size=1200,800',
                            'file://' + os.path.abspath(html_path)
                        ]
                        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        image_paths.append(output_path)
                        print(f"Converted {html_path} to image using Chrome headless")
                    except subprocess.SubprocessError as e:
                        print(f"Error converting {html_path} with Chrome: {e}")
                else:
                    print("No suitable HTML to image conversion tool found (wkhtmltoimage or Chrome/Chromium)")
                    break
        except Exception as e:
            print(f"Error during HTML to image conversion: {e}")
        
        return image_paths
    
    def load_training_plan(self, file_path='training_plan.md'):
        """Load training plan from markdown file"""
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                training_plan = f.read()
            return training_plan
        except Exception as e:
            print(f"Warning: Could not load training plan: {e}")
            return None
    
    def analyze_activities(self, days=7, activity_type='Ride', activity_id=None, 
                           include_timeseries=True, sample_rate=30, max_points=500,
                           timeseries_fields=None, use_visualizations=True, include_images=False,
                           max_images=3, convert_html=True):
        """Analyze activities and provide coaching insights"""
        try:
            # Format activity data
            activities_data = self.format_activity_data(
                activity_id=activity_id, 
                days=days, 
                activity_type=activity_type, 
                include_timeseries=include_timeseries, 
                sample_rate=sample_rate,
                max_points=max_points,
                timeseries_fields=timeseries_fields,
                use_visualizations=use_visualizations,
                include_images=include_images,
                max_images=max_images,
                convert_html=convert_html
            )
            
            if not activities_data:
                return "No activities found for analysis."
            
            # Load training plan
            training_plan = self.load_training_plan()
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system", 
                    "content": """You are an expert cycling coach with deep knowledge of training methodologies, 
                    physiology, and performance analysis. Analyze the provided cycling data and training plan 
                    to give structured, actionable insights and recommendations. Be specific, data-driven, and 
                    practical in your analysis. The data includes information about activities, including links 
                    to visualizations that have been generated for each activity."""
                },
                {
                    "role": "user",
                    "content": f"""
                    # Training Plan
                    {training_plan if training_plan else "No training plan provided."}
                    
                    # Activities Data (past {days} days)
                    {json.dumps(activities_data, indent=2)}
                    
                    Please provide a comprehensive analysis with the following structure:
                    
                    1. High-level summary of the analyzed timeframe
                    2. Session-by-session analysis
                    3. Detailed analysis of intervals and climbs
                    4. Recommendations for upcoming sessions
                    5. Suggested modifications to the training plan (if applicable)
                    """
                }
            ]
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during analysis: {str(e)}"
    
    def save_analysis(self, analysis, output_dir='data/analysis'):
        """Save analysis to a file"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{output_dir}/analysis_{timestamp}.md"
            
            with open(filename, 'w') as f:
                f.write(analysis)
            
            return filename
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return None 