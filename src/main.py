import os
import argparse
from strava_api import StravaAPI
from analyzer import ActivityAnalyzer

def main():
    """Main function to run the cycling coach assistant"""
    parser = argparse.ArgumentParser(description='AI Cycling Coach Assistant')
    parser.add_argument('--days', type=int, default=7, help='Number of days to fetch data for')
    parser.add_argument('--analyze_only', action='store_true', help='Skip data fetching and only analyze existing data')
    parser.add_argument('--activity_type', type=str, default='Ride', help='Activity type to analyze (default: Ride)')
    
    args = parser.parse_args()
    
    print("AI Cycling Coach Assistant")
    print("=========================")
    
    # Check if config directory exists
    if not os.path.exists('config/.env') and not args.analyze_only:
        print("Strava API credentials not found.")
        print("Please run the following command to set up Strava API authentication:")
        print("  python src/strava_auth.py")
        print("\nThis will guide you through the process of creating a Strava API application")
        print("and authenticating with your Strava account.")
        return
    
    # Fetch data from Strava API
    if not args.analyze_only:
        print(f"\nFetching activities from the past {args.days} days...")
        strava = StravaAPI()
        activities = strava.get_activities(days=args.days)
        
        if activities:
            print(f"Retrieved {len(activities)} activities")
            
            # Parse activities and save to CSV
            activities_df = strava.parse_activities(activities)
            strava.save_activities(activities_df)
        else:
            print("No activities found or error fetching data")
    
    # Analyze data
    print("\nAnalyzing activity data...")
    analyzer = ActivityAnalyzer()
    
    if analyzer.df is not None:
        # Print summary statistics for the specific activity type
        activity_df = analyzer.filter_activity_type(args.activity_type)
        if activity_df is not None and len(activity_df) > 0:
            stats = analyzer.summary_stats(activity_df)
            if stats:
                print(f"\n{args.activity_type} Activity Summary:")
                for key, value in stats.items():
                    print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
            
            # Generate plots
            analyzer.plot_weekly_distance(args.activity_type)
            analyzer.plot_heartrate_zones(args.activity_type)
            analyzer.training_load_analysis(args.activity_type)
        else:
            print(f"No {args.activity_type} activities found for analysis")

if __name__ == "__main__":
    main() 