"""
Test script for visualization-based OpenAI analysis.

This script tests the visualization-based approach for OpenAI integration.
"""

import os
import sys
import json
from pathlib import Path
import argparse
import glob

from src.openai_integration import OpenAICoach

def list_available_visualizations():
    """List all available visualization files in the data directory"""
    print("Searching for available visualization files...")
    
    # Look for HTML files
    html_files = []
    for root, dirs, files in os.walk('data'):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files:")
    for file in html_files:
        print(f"  - {file}")
    
    # Look for image files
    image_files = []
    for root, dirs, files in os.walk('data'):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join(root, file))
    
    print(f"\nFound {len(image_files)} image files (showing first 10):")
    for file in image_files[:10]:
        print(f"  - {file}")
    if len(image_files) > 10:
        print(f"  ... and {len(image_files) - 10} more")
    
    return html_files, image_files

def test_visualizations(days=7, activity_type='Ride', activity_id=None, 
                        include_images=True, max_images=3, convert_html=True):
    """Test visualization-based activity data formatting"""
    print(f"Testing visualization-based formatting for past {days} days, activity type: {activity_type}")
    
    # First, list all available visualizations
    html_files, image_files = list_available_visualizations()
    
    # Get list of activities
    activities_path = 'data/activities.csv'
    if os.path.exists(activities_path):
        import pandas as pd
        activities_df = pd.read_csv(activities_path)
        if len(activities_df) > 0:
            print(f"\nAvailable activities (showing first 5):")
            for i, (_, activity) in enumerate(activities_df.head().iterrows()):
                print(f"  - ID: {activity['id']}, Name: {activity['name']}")
    
    # Test OpenAI coach
    coach = OpenAICoach()
    activities_data = coach.format_activity_data(
        activity_id=activity_id, 
        days=days, 
        activity_type=activity_type,
        include_timeseries=False,  # Don't include timeseries data
        use_visualizations=True,   # Use dashboard visualizations
        include_images=include_images,
        max_images=max_images,
        convert_html=convert_html
    )
    
    if activities_data:
        print(f"\nSuccessfully formatted {len(activities_data)} activities")
        
        # Count total visualizations found
        total_visualizations = 0
        total_images = 0
        
        for activity in activities_data:
            print(f"\nActivity {activity['id']}: {activity['name']}")
            
            # Debug activity ID and name for file matching
            clean_name = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in activity['name'])
            print(f"  ID for matching: {activity['id']}")
            print(f"  Clean name for matching: {clean_name}")
            
            if 'visualizations' in activity:
                total_visualizations += len(activity['visualizations'])
                print(f"  Found {len(activity['visualizations'])} visualizations:")
                
                # Print paths to visualizations
                for i, viz_path in enumerate(activity['visualizations']):
                    print(f"    {i+1}. {viz_path}")
            else:
                print(f"  No visualizations found")
            
            if 'images' in activity:
                total_images += len(activity['images'])
                print(f"  Found {len(activity['images'])} encoded images:")
                
                # Print paths to images (not the base64 data)
                for i, img in enumerate(activity['images']):
                    print(f"    {i+1}. {img['path']}")
            else:
                print(f"  No images found")
        
        print(f"\nTotal visualizations found: {total_visualizations}")
        print(f"Total images encoded: {total_images}")
        
        # Estimate token usage
        if total_images > 0:
            # Rough estimate: each image is about 100KB base64 encoded, which is ~25K tokens
            estimated_image_tokens = total_images * 25000
            print(f"Estimated token usage for images: ~{estimated_image_tokens} tokens")
            print("Note: This is a rough estimate. Actual token usage depends on image size and complexity.")
    else:
        print("No activities found for the specified criteria")

def create_sample_visualizations():
    """Create sample visualization files for testing"""
    print("Creating sample visualization files...")
    
    # Create directories
    os.makedirs('data/figures/detailed', exist_ok=True)
    
    # Get list of activities
    activities_path = 'data/activities.csv'
    if not os.path.exists(activities_path):
        print("No activities.csv file found. Cannot create sample visualizations.")
        return
    
    import pandas as pd
    activities_df = pd.read_csv(activities_path)
    
    if len(activities_df) == 0:
        print("No activities found in activities.csv")
        return
    
    # Create sample files for each activity
    for _, activity in activities_df.head().iterrows():
        activity_id = str(int(activity['id']))
        activity_name = activity['name']
        clean_name = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in activity_name)
        
        # Create directory
        dir_path = f"data/figures/detailed/{activity_id}_{clean_name}"
        os.makedirs(dir_path, exist_ok=True)
        
        # Create sample HTML file
        with open(f"{dir_path}/dashboard.html", 'w') as f:
            f.write(f"<html><body><h1>Dashboard for {activity_name}</h1></body></html>")
        
        # Create sample image file
        with open(f"{dir_path}/activity_chart.png", 'w') as f:
            f.write(f"Sample image content for {activity_name}")
    
    print("Sample visualization files created successfully!")

def test_analysis_with_visualizations(days=7, activity_type='Ride', activity_id=None, save=True,
                                     include_images=False, max_images=2, convert_html=True):
    """Test OpenAI analysis with visualizations"""
    print(f"Testing OpenAI analysis with visualizations for past {days} days, activity type: {activity_type}")
    
    coach = OpenAICoach()
    analysis = coach.analyze_activities(
        days=days, 
        activity_type=activity_type, 
        activity_id=activity_id,
        include_timeseries=False,  # Don't include timeseries data
        use_visualizations=True,   # Use dashboard visualizations
        include_images=include_images,
        max_images=max_images,
        convert_html=convert_html
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
    parser = argparse.ArgumentParser(description='Test visualization-based OpenAI analysis')
    parser.add_argument('--test', choices=['visualizations', 'analysis', 'all', 'list', 'create_samples'], 
                        default='all', help='Test to run')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--type', default='Ride', help='Activity type')
    parser.add_argument('--id', default=None, help='Specific activity ID')
    parser.add_argument('--save', action='store_true', default=True, help='Save analysis to file')
    parser.add_argument('--images', action='store_true', default=False,
                        help='Include base64-encoded images of visualizations')
    parser.add_argument('--max-images', type=int, default=2,
                        help='Maximum number of images per activity')
    parser.add_argument('--convert-html', action='store_true', default=True,
                        help='Convert HTML dashboards to images')
    parser.add_argument('--no-convert-html', action='store_false', dest='convert_html',
                        help='Do not convert HTML dashboards to images')
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs('data/analysis', exist_ok=True)
    
    if args.test == 'list':
        list_available_visualizations()
    elif args.test == 'create_samples':
        create_sample_visualizations()
    elif args.test == 'visualizations' or args.test == 'all':
        test_visualizations(args.days, args.type, args.id, args.images, args.max_images, args.convert_html)
        print("\n" + "-" * 50 + "\n")
    
    if args.test == 'analysis' or args.test == 'all':
        test_analysis_with_visualizations(args.days, args.type, args.id, args.save, 
                                         args.images, args.max_images, args.convert_html)

if __name__ == "__main__":
    main() 