# CyclingCoach

**CyclingCoach** is an open-source tool for cyclists who want to analyze their Strava data, visualize their rides, and track their training progress—all with full control and privacy. It generates beautiful, interactive dashboards and supports user-defined heart rate and power zones.

---

## 🚴‍♂️ Features
- **Strava Integration**: Fetch and analyze your activities directly from Strava.
- **Interactive Dashboards**: Visualize heart rate, speed, altitude, route maps, and more.
- **User-Specified Zones**: Personalize your heart rate and power zones in a simple YAML file.
- **Training Load & Trends**: Track your training load and performance over time.
- **Detailed & Basic Analysis**: Run quick summaries or deep-dive into each activity.
- **AI Coaching**: Get personalized insights and recommendations using OpenAI's models.
- **Open Source & Extensible**: Easy to contribute, adapt, and extend.

---

## 🚀 Quickstart

### 1. Clone the repo
```sh
git clone https://github.com/yourusername/CyclingCoach.git
cd CyclingCoach
```

### 2. Install dependencies
We recommend using a virtual environment:
```sh
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Authenticate with Strava
Run the setup command and follow the prompts:
```sh
coach setup
```
This will guide you through authenticating with Strava and saving your API credentials.

### 4. Set up OpenAI API key
Add your OpenAI API key to `config/.env`:
```
OPENAI_API_KEY=your_api_key_here
```

---

## 🏁 Usage

### Fetch and analyze your rides
- **Fetch activities:**
  ```sh
  coach fetch --days 30
  ```
- **Basic analysis:**
  ```sh
  coach basic --days 30
  ```
- **Detailed analysis (all rides):**
  ```sh
  coach detailed --all
  ```
- **AI coaching analysis:**
  ```sh
  coach analyze --days 30
  ```
- **Full workflow (fetch, basic, detailed, AI analysis):**
  ```sh
  coach all --all
  ```

Results and visualizations are saved in the `data/figures/` and `data/figures/detailed/` folders. AI analysis is saved to `data/analysis/`.

---

## 🤖 AI Coaching
The AI coaching feature uses OpenAI's models to provide personalized insights and recommendations based on your activities and training plan.

### Training Plan
Create a `training_plan.md` file in the root directory to provide context for the AI coach. The AI will analyze your activities against this plan and suggest adjustments.

### Controlling Data Input
The AI coach can analyze your activities in different ways. You can choose between using:

1. **Dashboard Visualizations** (recommended): Uses links to the generated dashboards and visualizations
2. **Raw Timeseries Data**: Uses sampled timeseries data from your activities
3. **Static Images**: Includes base64-encoded images of your activity visualizations

```sh
# Use dashboard visualizations (default, most token-efficient)
coach analyze --days 30 --visualizations

# Use raw timeseries data instead
coach analyze --days 30 --no-visualizations

# Include static images of visualizations (WARNING: significantly increases token usage)
coach analyze --days 30 --images --max-images 1
```

#### Visualization Options:
- `--visualizations/--no-visualizations`: Use dashboard visualizations instead of raw data (default: use visualizations)
- `--images/--no-images`: Include base64-encoded images of visualizations (default: no images)
- `--max-images`: Maximum number of images per activity (default: 3)
- `--convert-html/--no-convert-html`: Convert HTML dashboards to images (default: convert)

> **⚠️ Warning about images**: Including images can dramatically increase token usage. Each image can use approximately 25,000 tokens. For example, 4 images would use around 100,000 tokens, which may exceed API limits. Use sparingly or with a small `--max-images` value.

#### HTML-to-Image Conversion
When using the `--images` option with `--convert-html` (default), the tool will:

1. Find HTML dashboard files for each activity
2. Convert these HTML files to PNG images using either:
   - wkhtmltoimage (if installed)
   - Chrome/Chromium in headless mode (if available)
3. Encode these images as base64 and include them in the OpenAI API request

This allows the AI model to actually "see" your dashboards and provide more informed analysis. To use this feature, you need either:
- wkhtmltoimage: `brew install wkhtmltopdf` (macOS) or `apt-get install wkhtmltopdf` (Linux)
- Google Chrome or Chromium browser installed on your system

#### Timeseries Data Options:
If using raw timeseries data (`--no-visualizations`), you can control:
- `--timeseries/--no-timeseries`: Include or exclude timeseries data (default: include)
- `--sample-rate`: Sample rate for timeseries data, every N points (default: 30)
- `--max-points`: Maximum number of data points per activity (default: 500)
- `--fields`: Comma-separated list of fields to include (default: time,distance,heartrate,altitude,velocity_smooth,grade_smooth)

### Analysis Output
The AI coach provides:
1. High-level summary of the analyzed timeframe
2. Session-by-session analysis
3. Detailed analysis of intervals and climbs
4. Recommendations for upcoming sessions
5. Suggested modifications to the training plan

---

## 🛠️ Personalization: Your Zones

You can define your own heart rate and power zones in `config/zones.yaml`:

```yaml
hr_zones:
  - name: Z1
    min: 0
    max: 124
  - name: Z2
    min: 125
    max: 144
  - name: Z3
    min: 145
    max: 164
  - name: Z4
    min: 165
    max: 172
  - name: Z5
    min: 173
    max: 178
  - name: Z6
    min: 179
    max: 185

power_zones: []
```

Edit these values to match your personal training zones. The dashboard will use these for zone-based analysis and pie charts.

---

## 📂 Outputs
- **Summary plots**: `data/figures/`
- **Detailed dashboards**: `data/figures/detailed/<activity_name>_<datetime>/dashboard.html`
- **Raw and processed data**: `data/streams/`, `data/detailed/`
- **AI coaching analysis**: `data/analysis/analysis_<datetime>.md`

Open the HTML dashboards in your browser for interactive exploration.

---


**Happy riding and analyzing!** 