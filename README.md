# AI Cycling Coach Assistant 🚴‍♂️

An intelligent cycling coach assistant that fetches your workout data from Strava, analyzes it, and helps you track your training progress.

## Features

- Authenticate and connect with Strava API
- Download activity data for the past week (or custom time period)
- Parse and analyze cycling workouts
- Generate interactive dashboards and visualizations:
  - Weekly distance and training load
  - Heart rate zones analysis
  - Detailed activity dashboards with maps
  - Power curves and metrics (if available)
  - Advanced performance analytics
- Support for custom training plans

## Prerequisites

- Python 3.7+
- A Strava account
- A Strava API application (create one at https://www.strava.com/settings/api)

## Installation

### Using pip

```
pip install -e .
```

### From source

1. Clone the repository:
```
git clone https://github.com/yourusername/CyclingCoach.git
cd CyclingCoach
```

2. Install the package in development mode:
```
pip install -e .
```

## Getting Started

### 1. Setup the application:

```
cyclingcoach setup
```

This will create necessary directories and guide you through the Strava API authentication process.

### 2. Authenticate with Strava API:

If you need to re-authenticate:

```
cyclingcoach auth
```

Follow the prompts to create a Strava API application and complete the authentication process. This will create a `.env` file in the `config` directory with your access tokens.

## Usage

### Quick all-in-one analysis:

Run complete analysis on all your activities from the past week:

```
cyclingcoach all
```

This command will:
1. Fetch your latest activities from Strava
2. Run basic analysis and generate summary statistics
3. Create detailed activity dashboards for each workout
4. Save all results to the data directory

### Fetch recent activities:

```
cyclingcoach fetch --days 14
```

### Run basic analysis on existing data:

```
cyclingcoach basic
```

### Analyze a specific type of activity:

```
cyclingcoach basic --activity_type "Run"
```

### Get detailed activity dashboards:

#### List available activities:

```
cyclingcoach detailed
```

#### Analyze a specific activity:

```
cyclingcoach detailed --activity_id <ID>
```

#### Analyze all recent activities:

```
cyclingcoach detailed --all
```

#### Analyze activities of a specific type:

```
cyclingcoach detailed --activity_type "Ride" --all
```

## Interactive Dashboards

The detailed analysis includes interactive dashboards with:

- Combined heart rate, power, cadence, and speed visualizations
- Route maps with color coding for altitude and speed
- Heart rate zone distribution charts
- Performance metrics tables
- Altitude profiles

Each dashboard is saved as an interactive HTML file in `data/figures/detailed/<activity_id>/dashboard.html`.

## Data Storage

- Activity data is stored in CSV format in the `data` directory
- Detailed activity data is stored in JSON format in the `data/detailed` directory
- Visualizations are saved in the `data/figures` directory:
  - Basic plots in `data/figures/`
  - Detailed dashboards in `data/figures/detailed/<activity_id>/`

## Training Plan

The project includes a training plan template in `training_plan.md` that can be customized for your specific goals.

## Development

### Project Structure

```
CyclingCoach/
├── cyclingcoach/      # Package code
│   ├── __init__.py
│   └── cli.py         # Command line interface
├── src/               # Core functionality 
│   ├── __init__.py
│   ├── analyzer.py    # Basic analysis
│   ├── detailed_activity.py  # Detailed analysis and dashboards
│   ├── strava_api.py  # Strava API interaction
│   └── strava_auth.py # Authentication
├── data/              # Data storage
├── config/            # Configuration files
├── pyproject.toml     # Package configuration
└── README.md
```

## Future Development

- Integration with training plans to compare actual vs. planned workouts
- Personalized workout recommendations based on previous activities
- Recovery and readiness metrics
- Performance trend analysis
- Integration with other fitness data sources

## License

MIT 