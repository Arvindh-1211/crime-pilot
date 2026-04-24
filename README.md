# NCRP Intelligent Cybercrime Complaint Filing Assistant

An AI-powered chatbot assistant that helps Indian citizens file cybercrime complaints on the National Cybercrime Reporting Portal (NCRP). The assistant detects fraud types from free-text descriptions, guides users through filling complaint details, validates all fields, checks for duplicates, and outputs a structured JSON complaint.

## Features

- **Multi-turn Conversational Chatbot**: Guided complaint filing through natural conversation
- **Fraud Type Detection**: Automatically classify cybercrime cases (UPI Fraud, Vishing, Phishing, Investment Scam, Sextortion)
- **Slot-Based Information Collection**: Collects required details one at a time with validation
- **Duplicate Detection**: Prevents duplicate complaints using hash and semantic similarity
- **Evidence Upload**: Allow users to upload supporting files (images, PDFs)
- **Severity Scoring**: Calculate case severity based on amount and evidence quality
- **Bilingual Support**: Works with English and Hinglish (Hindi-English mix)

## Tech Stack

### Backend
- Python 3.11
- FastAPI
- Uvicorn
- Google Gemini 1.5 Flash (LLM)
- sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- scikit-learn, numpy
- In-memory storage (no database)

### Frontend
- React 18
- Tailwind CSS
- Vite
- Axios

## Prerequisites

- **Python 3.11** or higher
- **Node.js 18** or higher
- **Google Gemini API Key** (for LLM functionality)

## Setup Instructions

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set Gemini API Key (required for LLM functionality)
# On Windows:
set GEMINI_API_KEY=your_google_gemini_api_key_here

# On Linux/Mac:
export GEMINI_API_KEY=your_google_gemini_api_key_here

# Run the server
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Open `http://localhost:5173` in your browser
2. The assistant will greet you and ask about your incident
3. Describe your cybercrime in English or Hinglish
4. Answer questions about the incident details
5. Upload evidence if available
6. Review and submit your complaint

## Demo Scenarios

### Scenario 1: UPI Fraud
```
User: Maine Google Pay se 5000 rupees ka transaction kiya tha jisme pata nahi kisne kiya
Assistant: I understand this involves a UPI transaction. Can you tell me when this incident occurred?

User: Kal raat ko hua tha
Assistant: Please provide the date in DD-MM-YYYY format. For example: 23-04-2025

User: 23-04-2025
Assistant: What amount did you lose?

User: 50000 rupees
...
```

### Scenario 2: Vishing
```
User: Mene ek call kiya tha jisme koi bank wala bana ke paise mang rahe the
Assistant: I see this might be a vishing (voice phishing) case. Can you tell me the caller's phone number?

User: 8888777766
Assistant: Invalid phone number. Please enter 10-digit Indian mobile (starting with 6-9)

User: 9876543210
...
```

### Scenario 3: Phishing
```
User: Mujhe ek email aaya tha jisme fake bank website ka link tha
Assistant: This appears to be a phishing attempt. When did you receive this email?

User: 20 April ko
Assistant: Please provide the date in DD-MM-YYYY format. For example: 20-04-2025

User: 20-04-2025
...
```

## API Endpoints

### Chat
- `POST /chat/start` - Initialize a new session
- `POST /chat/message` - Send a message

### Complaint
- `POST /complaint/submit` - Submit completed complaint
- `GET /complaint/{id}` - Get complaint by ID

### Upload
- `POST /upload/evidence` - Upload evidence file (JPG/PNG/PDF)

## Fraud Categories

| Category | Mandatory Fields |
|----------|-----------------|
| UPI_FRAUD | incident_date, amount_lost, upi_transaction_id, suspect_upi_id, platform |
| VISHING | incident_date, amount_lost, caller_number, bank_name |
| PHISHING | incident_date, phishing_url, data_compromised |
| INVESTMENT_SCAM | incident_date, amount_invested, platform_name, recruiter_contact |
| SEXTORTION | incident_date, platform_used, suspect_contact |

## Known Limitations

1. **In-memory storage**: All data resets when the server restarts
2. **5 fraud categories**: Currently supports only these categories
3. **Gemini API dependency**: LLM functionality requires valid API key
4. **Single session**: No persistence across multiple user sessions
5. **File uploads**: Stored in memory (for demo purposes only)

## Error Handling

- Gemini API failures return hardcoded fallback messages
- Invalid slot values re-ask the same question
- Session validation prevents unauthorized access

## License

MIT License
