# CyclingCoach 🚴‍♂️

An intelligent cycling coach assistant that fetches your workout data from Strava, analyzes it, and generates interactive dashboards to help you track your training progress.

## Features

- Authenticate with the Strava API to access your cycling data
- Download and store your recent cycling activities 
- Analyze your rides with detailed metrics and visualizations:
  - Weekly distance and time summaries
  - Heart rate zone distribution
  - Interactive maps with elevation and speed data
  - Power metrics (if power data is available)
  - Comprehensive performance dashboards

## Installation

### Prerequisites

- Python 3.7+
- A Strava account
- Strava API credentials (from https://www.strava.com/settings/api)

### Setup

1. Clone the repository:
```
git clone https://github.com/tomcastigl/CyclingCoach.git
cd CyclingCoach
```

2. Install the package and dependencies:
```
pip install -e .
```

## Usage

CyclingCoach provides a convenient command-line interface for all operations:

### Setup and Authentication

Initialize the application and authenticate with Strava:

```
cyclingcoach setup
```

If you need to re-authenticate later:

```
cyclingcoach auth
```

### Fetching Activities

Download your recent cycling activities:

```
cyclingcoach fetch --days 7
```

### Analysis Options

Run a quick analysis on your recent activities:

```
cyclingcoach basic
```

Generate detailed interactive dashboards:

```
cyclingcoach detailed --all
```

### All-in-One Command

For a complete workflow (fetch, analyze, create dashboards):

```
cyclingcoach all
```

## Interactive Dashboards

The application generates Plotly-based interactive dashboards that include:

- Combined visualizations of heart rate, power, cadence, and speed
- Color-coded route maps showing elevation and intensity
- Heart rate zone distribution charts
- Performance metrics tables
- Altitude profiles

Dashboards are saved as HTML files in `data/figures/detailed/<activity_id>/dashboard.html`.

## Project Structure

```
CyclingCoach/
├── src/               # Core functionality 
│   ├── analyzer.py    # Basic activity analysis
│   ├── detailed_activity.py  # Advanced analysis and dashboards
│   ├── strava_api.py  # Strava API interaction
│   └── strava_auth.py # Authentication handling
├── cyclingcoach/      # CLI interface
├── data/              # Activity data storage
│   ├── activities/    # Basic activity data (CSV)
│   ├── detailed/      # Detailed activity data (JSON)
│   └── figures/       # Generated visualizations
├── config/            # Configuration files and credentials
└── pyproject.toml     # Package configuration
```

## Data Storage

- Basic activity summaries are stored as CSV files
- Detailed activity data is stored in JSON format
- All visualizations are saved as HTML files for interactive viewing

## Future Development

- Markdown export of activity data for AI-powered analysis
- Training plan integration to compare actual vs. planned workouts
- Personalized workout recommendations based on training history
- Recovery and fatigue tracking
- Performance trend analysis

## License

MIT 