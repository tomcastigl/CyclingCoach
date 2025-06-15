# CyclingCoach

**CyclingCoach** is an open-source tool for cyclists who want to analyze their Strava data, visualize their rides, and track their training progress—all with full control and privacy. It generates beautiful, interactive dashboards and supports user-defined heart rate and power zones.

---

## 🚴‍♂️ Features
- **Strava Integration**: Fetch and analyze your activities directly from Strava.
- **Interactive Dashboards**: Visualize heart rate, speed, altitude, route maps, and more.
- **User-Specified Zones**: Personalize your heart rate and power zones in a simple YAML file.
- **Training Load & Trends**: Track your training load and performance over time.
- **Detailed & Basic Analysis**: Run quick summaries or deep-dive into each activity.
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
- **Full workflow (fetch, basic, detailed):**
  ```sh
  coach all
  ```

Results and visualizations are saved in the `data/figures/` and `data/figures/detailed/` folders.

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

Open the HTML dashboards in your browser for interactive exploration.

---


**Happy riding and analyzing!** 