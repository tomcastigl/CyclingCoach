"""
Command Line Interface for CyclingCoach.

This module provides a command-line interface to access
the core functionality of the CyclingCoach application.
"""

import argparse
import os
import sys
import json
from pathlib import Path

# Import core functionality
try:
    from src import strava_api, analyzer, detailed_activity
except ImportError:
    # Adjust import path if running as a package
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src import strava_api, analyzer, detailed_activity


def setup_dirs():
    """Create necessary directories if they don't exist"""
    dirs = [
        'data',
        'data/detailed',
        'data/streams',
        'data/figures',
        'data/figures/detailed',
        'config'
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("Directory structure created.")


def check_auth():
    """Check if authentication is configured"""
    if not os.path.exists('config/.env'):
        print("Strava API credentials not found. Running authentication...")
        # Import authenticate function only when needed
        from src.strava_auth import main as authenticate
        authenticate()
    else:
        print("Strava API credentials found.")
        # Test the credentials
        api = strava_api.StravaAPI()
        if api.access_token:
            print("Authentication successful!")
        else:
            print("Authentication failed. Please re-authenticate.")
            # Import authenticate function only when needed
            from src.strava_auth import main as authenticate
            authenticate()


def fetch_activities(days=7, activity_type=None):
    """Fetch activities from Strava"""
    print(f"Fetching activities from the past {days} days...")
    api = strava_api.StravaAPI()
    activities = api.get_activities(days=days)
    
    if activities:
        print(f"Retrieved {len(activities)} activities")
        df = api.parse_activities(activities)
        if df is not None:
            if activity_type:
                df = df[df['type'] == activity_type]
                print(f"Filtered to {len(df)} {activity_type} activities")
            
            # Save to CSV
            os.makedirs('data', exist_ok=True)
            df.to_csv('data/activities.csv', index=False)
            print("Activities saved to data/activities.csv")
            return df
    
    print("No activities found.")
    return None


def analyze_basic(days=7, activity_type='Ride'):
    """Run basic analysis on activities"""
    print("\nRunning basic analysis...")
    
    # Make sure we have activities data
    if not os.path.exists('data/activities.csv'):
        fetch_activities(days=days, activity_type=activity_type)
    
    analyzer_obj = analyzer.ActivityAnalyzer()
    
    if analyzer_obj.df is not None:
        # Print summary statistics
        if activity_type:
            filtered_df = analyzer_obj.filter_activity_type(activity_type)
            stats = analyzer_obj.summary_stats(filtered_df)
        else:
            stats = analyzer_obj.summary_stats()
        
        if stats:
            print(f"\n{activity_type} Activity Summary:")
            for key, value in stats.items():
                print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        
        # Generate plots
        analyzer_obj.plot_weekly_distance(activity_type=activity_type)
        analyzer_obj.plot_heartrate_zones(activity_type=activity_type)
        analyzer_obj.training_load_analysis(activity_type=activity_type)
        
        print("\nBasic analysis completed. Visualizations saved to data/figures/")
    else:
        print("No activities available for analysis.")


def analyze_detailed(activity_id=None, days=7, activity_type=None, all_activities=False):
    """Run detailed analysis on activities"""
    print("\nRunning detailed analysis...")
    
    detailed_analyzer = detailed_activity.DetailedActivityAnalyzer()
    
    if activity_id:
        # Process a specific activity
        print(f"Processing detailed data for activity {activity_id}")
        activity_data, streams_df = detailed_analyzer.process_activity_data(activity_id)
        
        if activity_data and streams_df is not None:
            analysis = detailed_analyzer.analyze_streams(streams_df, activity_data)
            if analysis:
                # Save analysis to JSON
                analysis_path = f'data/detailed/{activity_id}_analysis.json'
                with open(analysis_path, 'w') as f:
                    json.dump(analysis, f, cls=detailed_activity.NumpyEncoder)
                print(f"Analysis saved to {analysis_path}")
            
            # Generate visualizations
            detailed_analyzer.generate_activity_visualizations(streams_df, activity_id, activity_data.get('name', 'Activity'))
            print(f"Detailed analysis for activity {activity_id} completed.")
    else:
        # Process multiple activities
        activities_df = detailed_analyzer.get_activities(days=days, activity_type=activity_type)
        
        if activities_df is not None and len(activities_df) > 0:
            print(f"Found {len(activities_df)} activities to process")
            
            if all_activities:
                # Process all activities
                for idx, row in activities_df.iterrows():
                    activity_id = str(int(row['id']))
                    print(f"Processing activity {idx+1}/{len(activities_df)}: {activity_id} - {row['name']}")
                    activity_data, streams_df = detailed_analyzer.process_activity_data(activity_id)
                    
                    if activity_data and streams_df is not None:
                        analysis = detailed_analyzer.analyze_streams(streams_df, activity_data)
                        if analysis:
                            # Save analysis to JSON
                            analysis_path = f'data/detailed/{activity_id}_analysis.json'
                            with open(analysis_path, 'w') as f:
                                json.dump(analysis, f, cls=detailed_activity.NumpyEncoder)
                            print(f"Analysis saved to {analysis_path}")
                        
                        # Generate visualizations
                        detailed_analyzer.generate_activity_visualizations(streams_df, activity_id, row['name'])
                
                print("Detailed analysis for all activities completed.")
            else:
                # Just list activities
                print("\nAvailable activities:")
                for idx, row in activities_df.iterrows():
                    print(f"{idx+1}. {row['name']} ({row['type']}) - {row['start_date_local']} - ID: {int(row['id'])}")
                
                print("\nTo analyze a specific activity, use: coach detailed --activity_id <ID>")
                print("To analyze all activities in range, use: coach detailed --all")
        else:
            print("No activities found")


def analyze_all(days=7, activity_type='Ride'):
    """Run both basic and detailed analysis on all activities"""
    print(f"Running complete analysis for the past {days} days...")
    
    # First, fetch the latest activities
    fetch_activities(days=days, activity_type=activity_type)
    
    # Run basic analysis
    analyze_basic(days=days, activity_type=activity_type)
    
    # Run detailed analysis on all activities
    analyze_detailed(days=days, activity_type=activity_type, all_activities=True)
    
    print("\nComplete analysis finished! All results saved to data/ directory.")


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description='AI Cycling Coach Assistant')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup the application')
    
    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with Strava API')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch activities from Strava')
    fetch_parser.add_argument('--days', type=int, default=7, help='Number of days to fetch activities for')
    fetch_parser.add_argument('--activity_type', type=str, default=None, help='Type of activity to fetch (e.g., Ride, Run)')
    
    # Basic analysis command
    basic_parser = subparsers.add_parser('basic', help='Run basic analysis on activities')
    basic_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    basic_parser.add_argument('--activity_type', type=str, default='Ride', help='Type of activity to analyze (e.g., Ride, Run)')
    
    # Detailed analysis command
    detailed_parser = subparsers.add_parser('detailed', help='Run detailed analysis on activities')
    detailed_parser.add_argument('--activity_id', type=str, default=None, help='Specific activity ID to analyze')
    detailed_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    detailed_parser.add_argument('--activity_type', type=str, default=None, help='Type of activity to analyze (e.g., Ride, Run)')
    detailed_parser.add_argument('--all', action='store_true', help='Process all activities in range')
    
    # All-in-one analysis command
    all_parser = subparsers.add_parser('all', help='Run all analyses on activities')
    all_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    all_parser.add_argument('--activity_type', type=str, default='Ride', help='Type of activity to analyze (e.g., Ride, Run)')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_dirs()
        check_auth()
    elif args.command == 'auth':
        from src.strava_auth import main as authenticate
        authenticate()
    elif args.command == 'fetch':
        fetch_activities(days=args.days, activity_type=args.activity_type)
    elif args.command == 'basic':
        analyze_basic(days=args.days, activity_type=args.activity_type)
    elif args.command == 'detailed':
        analyze_detailed(
            activity_id=args.activity_id,
            days=args.days,
            activity_type=args.activity_type,
            all_activities=args.all
        )
    elif args.command == 'all':
        analyze_all(days=args.days, activity_type=args.activity_type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 