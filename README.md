# Surf Insight: Tidal Data and Surfing Experience Enhancements

Surf Insight is a cutting-edge Django-based web application designed to provide surfers with comprehensive tidal and weather data to enhance their surfing experience. Explore real-time insights and make informed decisions about your surf sessions. Learn more about the project on my portfolio page or explore the live application here.
Portfolio Page: https://paulmartin.vercel.app/portfolio/we-tide
Live App: wetide-b1e4fbe326fa.herokuapp.com

---

## Features

### 1. **Surfing Insights**
- **Tidal Data**: Integrates the NOAA API to fetch tide data from nearby research stations.
- **Weather Forecasts**: Utilizes the OpenWeatherMap API for real-time weather conditions.
- **Optimal Surfing Times**: Calculates ideal surfing windows based on tide levels, moon phases, and weather conditions.
- **Data Visualization**: Displays tide data and NOAA station locations on Google Maps with intuitive visualizations.

### 2. **Community Features**
- **Surf Session Logs**: Allows users to log and share their surf sessions with notes and experiences.
- **Session Filtering**: Enables filtering based on location, tide conditions, and weather.
- **Favorite Locations**: Users can save NOAA station data for quick access during future sessions.

---

## Getting Started

Follow the steps below to run Surf Insight locally:

### Prerequisites
- Python 3.9 or higher
- Django (check `requirements.txt` for the specific version)
- Access to the following APIs:
  - NOAA API
  - OpenWeatherMap API
  - Google Geocoding API

### Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/your-repo-url.git](https://github.com/enano1/we-tide.git)
   cd tide
   ```
2. **Set up a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4. **Set up your .env file with the following variables**:
    ```bash
    NOAA_API_KEY=your_noaa_api_key
    OPENWEATHER_API_KEY=your_openweather_api_key
    GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key
    ```
5. **Apply migrations and start the development server**:
    ```bash
    python manage.py migrate
    python manage.py runserver]
    ``` 

  
