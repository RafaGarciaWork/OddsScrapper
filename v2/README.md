# DraftKings Odds Scraper V2 - Testing & Web App

A comprehensive testing suite and web application for scraping DraftKings sports odds. This version includes improved scraping logic, multiple fallback methods, and a beautiful web interface for testing multiple URLs.

## 🚀 Features

- **Improved Scraping Logic**: Multiple CSS selector strategies with fallback methods
- **Web Application**: Beautiful, responsive web interface for testing
- **Multiple URL Support**: Test various DraftKings URLs simultaneously
- **Real-time Results**: Live scraping results with statistics
- **Error Handling**: Comprehensive error handling and logging
- **Preset URLs**: Pre-configured URLs for common sports and tournaments

## 📁 Project Structure

```
v2/
├── flask_app.py             # Flask backend with integrated scraper and API endpoints
├── templates/
│   └── web_app.html    # Web application frontend
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome Browser**: Ensure Chrome is installed on your system

3. **Run the Web Application**:
   ```bash
   python flask_app.py
   ```

4. **Access the Web App**: Open your browser and go to `http://localhost:5000`

## 🎯 Usage

### Web Application

1. **Single URL Testing**:
   - Enter a DraftKings URL in the input field
   - Click "Scrape Single URL"
   - View results in real-time

2. **Preset URL Testing**:
   - Click on any preset card to load the URL
   - Click "Scrape All Preset URLs" to test all presets
   - View comprehensive results and statistics

3. **Results View**:
   - See success/failure status for each URL
   - View scraped odds data
   - Check overall statistics

### Command Line Testing

The scraper functionality is integrated into the Flask app. For standalone testing, you can run the Flask app and use the API endpoints.

## 🛠️ Technical Improvements

### Issues Fixed from Original test_url.py:

1. **Wrong CSS Selectors**: 
   - ❌ Original: `[data-testid="offer-card"]`
   - ✅ Fixed: `span[data-testid="button-title-market-board"]` and `span[data-testid="button-odds-market-board"]`

2. **Hardcoded Team Detection**:
   - ❌ Original: Looking for specific team names like 'Chiefs', 'Eagles'
   - ✅ Fixed: Using proper CSS selectors for dynamic team detection

3. **Generic Odds Detection**:
   - ❌ Original: Unreliable text-based odds detection
   - ✅ Fixed: Multiple fallback methods with validation

4. **Missing Dependencies**:
   - ❌ Original: No dependency management
   - ✅ Fixed: Proper requirements.txt with webdriver-manager

### Scraping Strategy:

1. **Primary Method**: Use V1 working selectors
2. **Fallback Method**: Generic DraftKings patterns
3. **Text Extraction**: Regex-based extraction as last resort
4. **Validation**: Odds format validation (+/- numbers)

## 🌐 API Endpoints

### Flask Backend Endpoints:

- `GET /` - Serve the web application
- `POST /api/scrape` - Scrape a single URL
- `POST /api/scrape-multiple` - Scrape multiple URLs
- `GET /api/status` - Check server status

### Example API Usage:

```bash
# Scrape single URL
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl"}'

# Check status
curl http://localhost:5000/api/status
```

## 📊 Preset URLs

The web app includes preset URLs for testing:

- **NFL Super Bowl**: Championship odds
- **NFL Conference Winner**: Conference championship odds  
- **NFL Division Winner**: Division championship odds
- **NBA Championship**: NBA championship odds
- **MLB World Series**: MLB championship odds
- **NHL Stanley Cup**: NHL championship odds

## 🔍 Testing Results

Use the web application to test the scraper:

1. Start the Flask app: `python flask_app.py`
2. Open `http://localhost:5000` in your browser
3. Test various DraftKings URLs
4. View real-time results and statistics

## 🚨 Troubleshooting

### Common Issues:

1. **Chrome Driver Issues**:
   - Ensure Chrome browser is installed
   - The webdriver-manager will automatically download ChromeDriver

2. **No Odds Found**:
   - DraftKings may have changed their page structure
   - Check the console logs for debugging information
   - Try different URLs to verify the scraper is working

3. **Slow Scraping**:
   - The scraper includes delays to avoid being blocked
   - Use headless mode for faster execution

### Debug Mode:

The Flask app includes comprehensive logging. Check the console output for detailed debugging information when scraping URLs.

## 🔮 Future Enhancements

- **Database Integration**: Store scraped results
- **Scheduled Scraping**: Automated periodic scraping
- **More Sports**: Add additional sports and tournaments
- **Odds Processing**: Apply the same odds processing logic from V1
- **API Integration**: Connect to the CLM API for submission

## 📝 Notes

- The scraper includes multiple fallback methods to handle DraftKings' dynamic content
- Results are validated to ensure proper odds format
- The web app provides a user-friendly interface for testing
- All scraping includes proper error handling and logging

## 🤝 Contributing

To add new URLs or improve the scraper:

1. Add new preset URLs to the web app HTML
2. Test with the Flask app
3. Update the fallback methods in `flask_app.py` if needed
4. Use the web interface to verify functionality
