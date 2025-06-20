"""
Command Line Interface for CyclingCoach.

This module provides a command-line interface to access
the core functionality of the CyclingCoach application.
"""

import os
import sys
import json
from pathlib import Path
import click

from src import strava_api, analyzer, detailed_activity
from src.strava_auth import main as authenticate


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
    
    click.echo("Directory structure created.")


def check_auth():
    """Check if authentication is configured"""
    if not os.path.exists('config/.env'):
        click.echo("Strava API credentials not found. Running authentication...")
        authenticate()
    else:
        click.echo("Strava API credentials found.")
        # Test the credentials
        api = strava_api.StravaAPI()
        if api.access_token:
            click.echo("Authentication successful!")
        else:
            click.echo("Authentication failed. Please re-authenticate.")
            authenticate()


@click.group()
def cli():
    """CyclingCoach - Analyze your Strava cycling data."""
    pass


@cli.command()
def setup():
    """Setup the application and authenticate with Strava."""
    setup_dirs()
    check_auth()


@cli.command()
def auth():
    """Authenticate with Strava API."""
    authenticate()


@cli.command()
@click.option('--days', default=7, help='Number of days to fetch activities for')
@click.option('--activity_type', default=None, help='Type of activity to fetch (e.g., Ride, Run)')
def fetch(days, activity_type):
    """Fetch activities from Strava."""
    click.echo(f"Fetching activities from the past {days} days...")
    api = strava_api.StravaAPI()
    activities = api.get_activities(days=days)
    
    if activities:
        click.echo(f"Retrieved {len(activities)} activities")
        df = api.parse_activities(activities)
        if df is not None:
            if activity_type:
                df = df[df['type'] == activity_type]
                click.echo(f"Filtered to {len(df)} {activity_type} activities")
            
            # Save to CSV
            os.makedirs('data', exist_ok=True)
            df.to_csv('data/activities.csv', index=False)
            click.echo("Activities saved to data/activities.csv")
            return df
    
    click.echo("No activities found.")
    return None


@cli.command()
@click.option('--days', default=7, help='Number of days to analyze')
@click.option('--activity_type', default='Ride', help='Type of activity to analyze (e.g., Ride, Run)')
def basic(days, activity_type):
    """Run basic analysis on activities."""
    click.echo("\nRunning basic analysis...")
    
    # Make sure we have activities data
    if not os.path.exists('data/activities.csv'):
        fetch(days=days, activity_type=activity_type)
    
    analyzer_obj = analyzer.ActivityAnalyzer()
    
    if analyzer_obj.df is not None:
        # Print summary statistics
        if activity_type:
            filtered_df = analyzer_obj.filter_activity_type(activity_type)
            stats = analyzer_obj.summary_stats(filtered_df)
        else:
            stats = analyzer_obj.summary_stats()
        
        if stats:
            click.echo(f"\n{activity_type} Activity Summary:")
            for key, value in stats.items():
                click.echo(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        
        # Generate plots
        analyzer_obj.plot_weekly_distance(activity_type=activity_type)
        analyzer_obj.plot_heartrate_zones(activity_type=activity_type)
        analyzer_obj.training_load_analysis(activity_type=activity_type)
        
        click.echo("\nBasic analysis completed. Visualizations saved to data/figures/")
    else:
        click.echo("No activities available for analysis.")


@cli.command()
@click.option('--activity_id', default=None, help='Specific activity ID to analyze')
@click.option('--days', default=7, help='Number of days to analyze')
@click.option('--activity_type', default=None, help='Type of activity to analyze (e.g., Ride, Run)')
@click.option('--all', is_flag=True, help='Process all activities in range')
def detailed(activity_id, days, activity_type, all):
    """Run detailed analysis on activities."""
    click.echo("\nRunning detailed analysis...")
    
    detailed_analyzer = detailed_activity.DetailedActivityAnalyzer()
    
    if activity_id:
        # Process a specific activity
        click.echo(f"Processing detailed data for activity {activity_id}")
        activity_data, streams_df = detailed_analyzer.process_activity_data(activity_id)
        
        if activity_data and streams_df is not None:
            analysis = detailed_analyzer.analyze_streams(streams_df, activity_data)
            if analysis:
                # Save analysis to JSON
                analysis_path = f'data/detailed/{activity_id}_analysis.json'
                with open(analysis_path, 'w') as f:
                    json.dump(analysis, f, cls=detailed_activity.NumpyEncoder)
                click.echo(f"Analysis saved to {analysis_path}")
            
            # Generate visualizations
            detailed_analyzer.generate_activity_visualizations(activity_id, activity_data.get('name', 'Activity'), streams_df)
            click.echo(f"Detailed analysis for activity {activity_id} completed.")
    else:
        # Process multiple activities
        activities_df = detailed_analyzer.get_activities(days=days, activity_type=activity_type)
        
        if activities_df is not None and len(activities_df) > 0:
            click.echo(f"Found {len(activities_df)} activities to process")
            
            if all:
                # Process all activities
                for idx, row in activities_df.iterrows():
                    activity_id = str(int(row['id']))
                    click.echo(f"Processing activity {idx+1}/{len(activities_df)}: {activity_id} - {row['name']}")
                    activity_data, streams_df = detailed_analyzer.process_activity_data(activity_id)
                    
                    if activity_data and streams_df is not None:
                        analysis = detailed_analyzer.analyze_streams(streams_df, activity_data)
                        if analysis:
                            # Save analysis to JSON
                            analysis_path = f'data/detailed/{activity_id}_analysis.json'
                            with open(analysis_path, 'w') as f:
                                json.dump(analysis, f, cls=detailed_activity.NumpyEncoder)
                            click.echo(f"Analysis saved to {analysis_path}")
                        
                        # Generate visualizations
                        detailed_analyzer.generate_activity_visualizations(activity_id, row['name'], streams_df)
                
                click.echo("Detailed analysis for all activities completed.")
            else:
                # Just list activities
                click.echo("\nAvailable activities:")
                for idx, row in activities_df.iterrows():
                    click.echo(f"{idx+1}. {row['name']} ({row['type']}) - {row['start_date_local']} - ID: {int(row['id'])}")
                
                click.echo("\nTo analyze a specific activity, use: coach detailed --activity_id <ID>")
                click.echo("To analyze all activities in range, use: coach detailed --all")
        else:
            click.echo("No activities found")


@cli.command()
@click.option('--days', default=7, help='Number of days to analyze')
@click.option('--activity_type', default='Ride', help='Type of activity to analyze (e.g., Ride, Run)')
def all(days, activity_type):
    """Run all analyses on activities (fetch, basic, detailed)."""
    click.echo(f"Running complete analysis for the past {days} days...")
    
    # First, fetch the latest activities
    fetch.callback(days=days, activity_type=activity_type)
    
    # Run basic analysis
    basic.callback(days=days, activity_type=activity_type)
    
    # Run detailed analysis on all activities
    detailed.callback(days=days, activity_type=activity_type, activity_id=None, all=True)
    
    click.echo("\nComplete analysis finished! All results saved to data/ directory.")


if __name__ == "__main__":
    cli() 