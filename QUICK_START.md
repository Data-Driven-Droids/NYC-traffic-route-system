# 🚀 Quick Start Guide - NYC Route Optimizer

## ⚡ Get Running in 5 Minutes

### 1. Prerequisites Check
- ✅ Python 3.8+ installed
- ✅ Git repository cloned/downloaded
- ⏳ Google Cloud Platform account (we'll set this up)

### 2. Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install required packages
pip install -r requirements.txt
```

### 3. Google Maps API Setup (5 minutes)

#### Step A: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" → Name it "NYC Route Optimizer"
3. Enable billing (required for Maps APIs)

#### Step B: Enable APIs
In Google Cloud Console, go to "APIs & Services" → "Library" and enable:
- **Maps JavaScript API**
- **Places API (New)**  
- **Directions API**
- **Geocoding API**

#### Step C: Create API Key
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the key (looks like: `AIzaSyD...`)
4. **IMPORTANT**: Click "Restrict Key":
   - Application restrictions: HTTP referrers
   - Add: `localhost:8501/*`
   - API restrictions: Select the 4 APIs above

### 4. Configure Application
```bash
# Copy environment template
cp .env.example .env

# Edit .env file (use any text editor)
notepad .env  # Windows
# nano .env   # macOS/Linux
```

Add your API key to `.env`:
```
GOOGLE_MAPS_API_KEY=AIzaSyD...your_actual_key_here
```

### 5. Test Setup
```bash
python test_api.py
```

You should see:
```
🧪 NYC Route Optimizer - API Test Suite
✅ Configuration is valid
✅ Places API working
✅ Directions API working
✅ Address validation working
✅ NYC Bounds working
🎉 All tests passed!
```

### 6. Launch Application
```bash
streamlit run app.py
```

The app opens at: `http://localhost:8501`

## 🎯 First Test

Try these NYC addresses:
- **Start**: `Times Square, New York, NY`
- **End**: `Central Park, New York, NY`

Click "Find Best Routes" and you should see:
- Multiple route options
- Real-time traffic analysis
- Interactive map with route visualization
- Efficiency scores and recommendations

## 🚨 Troubleshooting

### "Configuration Error: GOOGLE_MAPS_API_KEY is required"
- Check `.env` file exists and contains your API key
- Ensure no quotes around the API key value

### "API request denied"
- Verify billing is enabled in Google Cloud Console
- Check API key restrictions allow `localhost:8501/*`
- Ensure all 4 APIs are enabled

### "No routes found"
- Use complete street addresses
- Ensure both addresses are in NYC
- Try popular landmarks like "Empire State Building"

### "Address not found or outside NYC area"
- Include "New York, NY" in addresses
- Use specific street addresses
- Try nearby intersections or landmarks

## 💡 Pro Tips

1. **Better Results**: Use specific street addresses instead of general areas
2. **Performance**: Results are cached for 5 minutes to improve speed
3. **Traffic**: Best results during peak hours when traffic varies most
4. **Alternatives**: Try different departure times for better routes

## 🔗 Useful Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Maps Platform Documentation](https://developers.google.com/maps/documentation)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 📞 Need Help?

1. Run `python test_api.py` to diagnose issues
2. Check the full [`README.md`](README.md) for detailed documentation
3. Review [`implementation_guide.md`](implementation_guide.md) for step-by-step setup

---

**🗽 Ready to optimize your NYC routes with real-time traffic analysis!**