"""
Test script for OpenAI integration.

This script tests the OpenAICoach class functionality.
"""

import os
import sys
import json
from pathlib import Path
import argparse

from src.openai_integration import OpenAICoach

def test_format_data(days=7, activity_type='Ride', activity_id=None, timeseries=True, 
                     sample_rate=30, max_points=500, timeseries_fields=None,
                     use_visualizations=True, include_images=False, max_images=10):
    """Test formatting activity data for LLM"""
    print(f"Testing data formatting for past {days} days, activity type: {activity_type}")
    
    coach = OpenAICoach()
    activities_data = coach.format_activity_data(
        activity_id=activity_id, 
        days=days, 
        activity_type=activity_type,
        include_timeseries=timeseries,
        sample_rate=sample_rate,
        max_points=max_points,
        timeseries_fields=timeseries_fields,
        use_visualizations=True,
        include_images=True,
        max_images=10
    )
    
    if activities_data:
        print(f"Successfully formatted {len(activities_data)} activities")
        # Print sample data
        print("\nSample data:")
        # Create a simplified version for display
        sample_data = activities_data[0].copy() if activities_data else {}
        print(sample_data.keys())
        # If timeseries data exists, just show its structure but not the full data
        if 'timeseries' in sample_data:
            timeseries_keys = list(sample_data['timeseries'].keys())
            timeseries_lengths = {k: len(sample_data['timeseries'][k]) for k in timeseries_keys}
            sample_data['timeseries'] = {
                'available_fields': timeseries_keys,
                'data_points': timeseries_lengths
            }
        
        # If images exist, just show paths but not the base64 data
        if 'images' in sample_data:
            image_paths = [img['path'] for img in sample_data['images']]
            sample_data['images'] = {
                'count': len(image_paths),
                'paths': image_paths
            }
        
        print(json.dumps(sample_data, indent=2))
    else:
        print("No activities found for the specified criteria")

def test_training_plan():
    """Test loading training plan"""
    print("Testing training plan loading")
    
    coach = OpenAICoach()
    training_plan = coach.load_training_plan()
    
    if training_plan:
        print("Training plan loaded successfully")
        print("\nFirst 200 characters:")
        print(training_plan[:200] + "...")
    else:
        print("No training plan found")

def test_analysis(days=7, activity_type='Ride', activity_id=None, save=False, timeseries=True, 
                  sample_rate=30, max_points=500, timeseries_fields=None,
                  use_visualizations=True, include_images=False, max_images=3):
    """Test OpenAI analysis"""
    print(f"Testing OpenAI analysis for past {days} days, activity type: {activity_type}")
    
    coach = OpenAICoach()
    analysis = coach.analyze_activities(
        days=days, 
        activity_type=activity_type, 
        activity_id=activity_id,
        include_timeseries=timeseries,
        sample_rate=sample_rate,
        max_points=max_points,
        timeseries_fields=timeseries_fields,
        use_visualizations=use_visualizations,
        include_images=include_images,
        max_images=max_images
    )
    
    if analysis:
        print("Analysis completed successfully")
        print("\nAnalysis preview:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
        if save:
            filename = coach.save_analysis(analysis)
            print(f"\nAnalysis saved to {filename}")
    else:
        print("Analysis failed or no activities found")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test OpenAI integration')
    parser.add_argument('--test', choices=['format', 'plan', 'analysis', 'all'], 
                        default='all', help='Test to run')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--type', default='Ride', help='Activity type')
    parser.add_argument('--id', default=None, help='Specific activity ID')
    parser.add_argument('--save', action='store_true', help='Save analysis to file')
    parser.add_argument('--timeseries', action='store_true', default=True, help='Include timeseries data')
    parser.add_argument('--no-timeseries', action='store_false', dest='timeseries', help='Exclude timeseries data')
    parser.add_argument('--sample-rate', type=int, default=30, help='Sample rate for timeseries data')
    parser.add_argument('--max-points', type=int, default=500, help='Maximum number of data points per activity')
    parser.add_argument('--fields', default='time,distance,heartrate,altitude,velocity_smooth,grade_smooth',
                        help='Comma-separated list of timeseries fields to include')
    parser.add_argument('--visualizations', action='store_true', default=True, 
                        help='Use dashboard visualizations instead of raw timeseries data')
    parser.add_argument('--no-visualizations', action='store_false', dest='visualizations',
                        help='Exclude dashboard visualizations')
    parser.add_argument('--images', action='store_true', default=False,
                        help='Include base64-encoded images of visualizations')
    parser.add_argument('--no-images', action='store_false', dest='images',
                        help='Exclude base64-encoded images')
    parser.add_argument('--max-images', type=int, default=3,
                        help='Maximum number of images per activity')
    
    args = parser.parse_args()
    
    # Parse timeseries fields
    timeseries_fields = args.fields.split(',') if args.fields else None
    
    # Create necessary directories
    os.makedirs('data/analysis', exist_ok=True)
    
    if args.test == 'format' or args.test == 'all':
        test_format_data(args.days, args.type, args.id, args.timeseries, 
                         args.sample_rate, args.max_points, timeseries_fields,
                         args.visualizations, args.images, args.max_images)
        print("\n" + "-" * 50 + "\n")
    
    if args.test == 'plan' or args.test == 'all':
        test_training_plan()
        print("\n" + "-" * 50 + "\n")
    
    if args.test == 'analysis' or args.test == 'all':
        test_analysis(args.days, args.type, args.id, args.save, args.timeseries,
                      args.sample_rate, args.max_points, timeseries_fields,
                      args.visualizations, args.images, args.max_images)

if __name__ == "__main__":
    main() 