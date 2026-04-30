# Banana Crop Grading AI Agent

An intelligent system to automatically grade banana crops based on images and videos for FPO (Farmer Producer Organization) export quality control.

## Features

✅ Image and video upload support
✅ Automated crop quality grading
✅ Disease/defect detection
✅ Quality scoring (Export Ready / Grade A / Grade B / Reject)
✅ Web dashboard for easy use
✅ API endpoints for integration (Boomi ready)
✅ Detailed grading reports

## Project Structure

```
banana-grading-ai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── config.py             # Configuration settings
├── models/               # AI models directory
├── uploads/              # Uploaded images/videos
├── static/               # CSS, JavaScript files
├── templates/            # HTML templates
├── agent/
│   ├── __init__.py
│   ├── grading_agent.py  # Main AI grading logic
│   ├── image_processor.py # Image processing
│   └── video_processor.py # Video processing
└── utils/
    ├── __init__.py
    └── helpers.py        # Utility functions
```

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 2GB RAM minimum
- 500MB disk space for models

## Installation & Setup (Step by Step)

### Step 1: Clone the Repository
```bash
git clone https://github.com/pnallaballe/ai_agent_test.git
cd ai_agent_test
```

### Step 2: Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Download AI Models
```bash
python download_models.py
```

### Step 5: Run the Application
```bash
python app.py
```

The application will start at: `http://localhost:5000`

## How to Use

1. **Open Web Interface**: Visit `http://localhost:5000` in your browser
2. **Upload Image**: Click "Upload Image" and select a banana crop image
3. **Get Results**: AI analyzes and provides:
   - Quality Grade (A/B/C/Reject)
   - Confidence Score
   - Detected Issues
   - Recommendations

## API Endpoints (For Boomi Integration)

### Upload & Grade Image
```
POST /api/grade-image
Content-Type: multipart/form-data
- file: [image file]

Response:
{
  "grade": "Grade A",
  "confidence": 0.95,
  "issues": [],
  "recommendation": "Ready for export",
  "timestamp": "2026-04-30T10:30:00Z"
}
```

### Upload & Grade Video
```
POST /api/grade-video
Content-Type: multipart/form-data
- file: [video file]

Response:
{
  "frames_analyzed": 120,
  "average_grade": "Grade A",
  "average_confidence": 0.92,
  "issues": ["Minor browning in 3 frames"],
  "recommendation": "Ready for export",
  "timestamp": "2026-04-30T10:30:00Z"
}
```

### Get Grading History
```
GET /api/history?limit=10&skip=0

Response:
{
  "total": 50,
  "items": [...]
}
```

## Grading Criteria

**Grade A (90-100% quality)**
- Perfect color (bright yellow)
- No defects or blemishes
- Proper size and shape
- Disease-free

**Grade B (75-89% quality)**
- Good color with minor variations
- Minor cosmetic blemishes
- Acceptable shape
- No disease

**Grade C (60-74% quality)**
- Average color
- Some visible defects
- Normal shape
- Minor fungal traces

**Reject (<60% quality)**
- Poor color
- Significant damage
- Disease present
- Unsuitable for export

## Learning Path (For You!)

This project teaches you:
1. **Week 1**: Python basics + Setup
2. **Week 2**: Image processing basics
3. **Week 3**: Understanding AI models
4. **Week 4**: API integration & testing

## Next Steps

- [ ] Install dependencies
- [ ] Download AI models
- [ ] Run test upload
- [ ] Integrate with Boomi
- [ ] Deploy to production

## Support & Documentation

Each Python file has detailed comments explaining:
- What the code does
- Why we're doing it
- How to modify it

## License

MIT License - Free for commercial use

## Contact

For questions or issues: pnallaballe@github.com

---

**Built with ❤️ for Farmer Producer Organizations**
