# 🗽 NYC Traffic-Aware Route Optimizer

A Streamlit web application that provides real-time traffic analysis and route recommendations for New York City using Google Maps APIs.

![NYC Route Optimizer](https://img.shields.io/badge/NYC-Route%20Optimizer-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Google Maps](https://img.shields.io/badge/Google%20Maps-API-yellow)

## 🌟 Features

- **Real-time Traffic Analysis**: Get current traffic conditions for all routes
- **Multiple Route Options**: Compare up to 5 different route alternatives
- **Efficiency Scoring**: Smart algorithm ranks routes by time, distance, and traffic
- **Interactive Maps**: Visual route display with Folium integration
- **Address Autocomplete**: Smart address suggestions with NYC validation
- **Traffic Delay Insights**: See exactly how much time traffic adds to your journey
- **Route Comparison**: Side-by-side analysis of all route options
- **Search History**: Keep track of your recent route searches

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Google Maps API key with billing enabled

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd nyc-route-optimizer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Cloud Setup

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable billing for your project

#### Enable Required APIs
Navigate to "APIs & Services" → "Library" and enable:
- **Maps JavaScript API**
- **Places API (New)**
- **Directions API**
- **Geocoding API**

#### Create API Key
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key
4. **Important**: Restrict the API key:
   - Application restrictions: HTTP referrers
   - Add `localhost:8501/*` for development
   - API restrictions: Select the 4 APIs above

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API key
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

### 4. Test Setup

```bash
# Run API tests
python test_api.py
```

You should see all tests pass:
```
🧪 NYC Route Optimizer - API Test Suite
==================================================
✅ Configuration is valid
✅ Places API working
✅ Directions API working
✅ Address validation working
✅ NYC Bounds working

🎉 All tests passed! Your API setup is working correctly.
```

### 5. Run Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Basic Usage

1. **Enter Addresses**: Type start and end addresses in NYC
2. **Address Validation**: The app validates addresses are in NYC boundaries
3. **Find Routes**: Click "Find Best Routes" to calculate options
4. **View Results**: See route comparison, map visualization, and recommendations

### Advanced Features

#### Search Options
- **Departure Time**: Choose "Now" or set custom departure time
- **Traffic Model**: Select optimistic, pessimistic, or best guess
- **Maximum Routes**: Control how many alternatives to calculate

#### Map Controls
- **Map Height**: Adjust display size
- **Traffic Layer**: Toggle real-time traffic overlay
- **Route Focus**: Highlight specific routes
- **Interactive Elements**: Click routes for detailed information

#### Understanding Results

**Efficiency Score**: 0-100 rating based on:
- Travel time with traffic (40% weight)
- Route distance (30% weight)
- Traffic delay impact (30% weight)

**Traffic Status**:
- 🟢 Light Traffic: <10% delay
- 🟡 Moderate Traffic: 10-25% delay
- 🟠 Heavy Traffic: 25-50% delay
- 🔴 Severe Traffic: >50% delay

## 🏗️ Project Structure

```
nyc-route-optimizer/
├── app.py                 # Main Streamlit application
├── test_api.py           # API testing script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── config/
│   ├── __init__.py
│   └── settings.py      # Configuration management
├── src/
│   ├── maps/
│   │   ├── places_api.py    # Google Places integration
│   │   ├── directions.py    # Route calculation
│   │   └── __init__.py
│   ├── ui/
│   │   ├── components.py    # UI components
│   │   ├── map_display.py   # Map visualization
│   │   └── __init__.py
│   ├── utils/
│   │   ├── validation.py    # Address validation
│   │   ├── helpers.py       # Utility functions
│   │   └── __init__.py
│   └── __init__.py
└── docs/
    ├── architecture_plan.md
    └── implementation_guide.md
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_MAPS_API_KEY` | Your Google Maps API key | Required |
| `NYC_BOUNDS_NORTH` | Northern boundary of NYC | 40.9176 |
| `NYC_BOUNDS_SOUTH` | Southern boundary of NYC | 40.4774 |
| `NYC_BOUNDS_EAST` | Eastern boundary of NYC | -73.7004 |
| `NYC_BOUNDS_WEST` | Western boundary of NYC | -74.2591 |
| `DEFAULT_CENTER_LAT` | Default map center latitude | 40.7589 |
| `DEFAULT_CENTER_LNG` | Default map center longitude | -73.9851 |
| `CACHE_DURATION` | API response cache time (seconds) | 300 |
| `MAX_ROUTES` | Maximum routes to calculate | 5 |

### Customization

You can modify the following in [`config/settings.py`](config/settings.py):
- NYC boundary coordinates
- Traffic model preferences
- Caching behavior
- Route scoring weights

## 🚨 Troubleshooting

### Common Issues

#### "Configuration Error: GOOGLE_MAPS_API_KEY is required"
- Ensure `.env` file exists with your API key
- Check API key format (no quotes needed)
- Verify the key is active in Google Cloud Console

#### "API request denied"
- Check API key restrictions in Google Cloud Console
- Ensure billing is enabled
- Verify required APIs are enabled

#### "No routes found"
- Confirm addresses are in NYC boundaries
- Try more specific street addresses
- Check internet connectivity

#### "Address not found or outside NYC area"
- Use complete street addresses
- Include "New York, NY" in address
- Try nearby landmarks or intersections

### API Quotas and Limits

**Free Tier Limits** (per month):
- Directions API: $200 credit (~40,000 requests)
- Places API: $200 credit (~100,000 requests)
- Geocoding API: $200 credit (~40,000 requests)

**Rate Limits**:
- 50 requests per second per API
- 1,000 requests per 100 seconds per user

### Performance Tips

1. **Use Caching**: Results are cached for 5 minutes by default
2. **Limit Routes**: Fewer route alternatives = faster response
3. **Specific Addresses**: More precise addresses = better results
4. **Off-Peak Usage**: Better performance during low-traffic times

## 🔒 Security

### API Key Security
- Never commit API keys to version control
- Use environment variables for configuration
- Implement API key restrictions in Google Cloud Console
- Monitor usage in Google Cloud Console

### Recommended Restrictions
- **Application restrictions**: HTTP referrers
- **Website restrictions**: Your domain(s)
- **API restrictions**: Only enable required APIs

## 🚀 Deployment

### Streamlit Cloud

1. Push code to GitHub repository
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add environment variables in Streamlit Cloud settings
4. Deploy application

### Heroku

```bash
# Create Procfile
echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# Deploy to Heroku
heroku create your-app-name
heroku config:set GOOGLE_MAPS_API_KEY=your_key_here
git push heroku main
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Maps Platform** for providing comprehensive mapping APIs
- **Streamlit** for the excellent web app framework
- **Folium** for interactive map visualizations
- **NYC Open Data** for boundary information

## 📞 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Run `python test_api.py` to verify setup
3. Review Google Cloud Console for API errors
4. Create an issue in the repository

## 🔮 Future Enhancements

- [ ] Public transit integration
- [ ] Historical traffic pattern analysis
- [ ] Route preferences (avoid tolls, highways)
- [ ] Multi-stop route optimization
- [ ] Weather impact consideration
- [ ] Mobile app version
- [ ] User accounts and saved routes
- [ ] Real-time traffic alerts

---

**Built with ❤️ for New York City travelers**