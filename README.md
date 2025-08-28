# Drone Directory - AI-Powered Company Scraper

A FastAPI-based web application that automatically scrapes and stores drone company information using AI-powered parsing.

## ✨ Features

### 🔍 Smart Scraping
- **Company Name Input**: Enter a company name (e.g., "DJI") and the system automatically searches for their official website
- **Direct URL Input**: Provide a direct website URL (e.g., "https://dji.com") for immediate scraping
- **AI-Powered Parsing**: Uses Google Gemini API to intelligently extract structured company data
- **Automatic Website Discovery**: DuckDuckGo integration to find company websites when only names are provided

### 📊 Data Extraction
- Company name and website
- Email addresses and phone numbers
- Physical addresses
- Company description and category
- Industry classification

### 🎨 Modern Web Interface
- Clean, responsive dashboard built with Tailwind CSS
- Real-time search functionality
- Detailed company information modal
- Error handling and success messages

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd drone-directory
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

3. **Run the application:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Open your browser:**
   - Dashboard: http://localhost:8000/ui/
   - API Docs: http://localhost:8000/docs

## 📖 Usage

### Web Interface

1. **Add New Company:**
   - Go to the dashboard
   - Enter either a company name or website URL
   - Click "🚀 Scrape Company Info"
   - The system will automatically detect the input type and proceed accordingly

2. **Search Companies:**
   - Use the search bar to find existing companies
   - Search by name, category, email, phone, or description

### API Endpoints

#### Scrape Company Information
```bash
# Scrape by company name
curl -X POST "http://localhost:8000/scrape-ai" \
  -H "Content-Type: application/x-encoding" \
  -d "query=DJI"

# Scrape by direct URL
curl -X POST "http://localhost:8000/scrape-ai" \
  -H "Content-Type: application/x-encoding" \
  -d "query=https://dji.com"
```

#### List Companies
```bash
curl "http://localhost:8000/companies/"
```

#### Search Companies
```bash
curl "http://localhost:8000/search?query=dji"
```

## 🧪 Testing

Run the test script to verify functionality:

```bash
python test_scraping.py
```

## 🏗️ Architecture

```
app/
├── main.py              # FastAPI application and routes
├── models.py            # SQLAlchemy database models
├── database.py          # Database connection and session
├── schemas.py           # Pydantic data validation schemas
├── crud.py             # Database CRUD operations
└── services/
    ├── scraper.py      # Main scraping orchestration
    ├── scraper_ai.py   # Web scraping and contact page detection
    └── ai_parser.py    # AI-powered text parsing using Gemini
```

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key for AI parsing

### Database
- SQLite database (`drone_directory.db`) - automatically created on first run
- Can be easily migrated to PostgreSQL or MySQL by updating `database.py`

## 🎯 How It Works

1. **Input Processing**: System detects whether input is a company name or URL
2. **Website Discovery**: If company name provided, searches DuckDuckGo for official website
3. **Content Scraping**: Fetches webpage content and looks for contact/about pages
4. **AI Parsing**: Uses Gemini API to extract structured company information
5. **Data Storage**: Saves parsed information to SQLite database
6. **User Interface**: Provides web dashboard for viewing and searching companies

## 🚨 Error Handling

- **Website Not Found**: Graceful fallback when company website can't be located
- **Scraping Failures**: User-friendly error messages for failed scraping attempts
- **API Rate Limits**: Handles Gemini API quota exceeded scenarios
- **Network Issues**: Timeout handling for slow-loading websites

## 🔮 Future Enhancements

- [ ] Batch scraping from CSV/Excel files
- [ ] Export functionality (CSV, JSON, PDF)
- [ ] Company data validation and verification
- [ ] Integration with business databases
- [ ] Advanced filtering and analytics
- [ ] Email notification system
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the error logs in the console
2. Verify your Gemini API key is valid
3. Ensure all dependencies are installed
4. Check network connectivity for web scraping

---

**Happy Scraping! 🚁✨**
