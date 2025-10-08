# MockExamify - Interactive Mock Exam Platform

A full-stack Python application for selling and hosting interactive mock exams with credit system, payments, and AI integration.

## Features

- 🎯 Interactive multiple-choice mock exams
- 💳 Credit-based monetization with Stripe payments
- 🤖 OpenRouter AI integration for explanations and content generation
- 📄 PDF generation for exam downloads
- 👥 User authentication and role-based access
- 🛠️ Admin dashboard for mock management
- 📊 User progress tracking and analytics

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: Supabase (PostgreSQL + Auth)
- **Payments**: Stripe
- **AI**: OpenRouter API
- **PDF Generation**: WeasyPrint/ReportLab

## Quick Start

### Prerequisites

- Python 3.8+
- Supabase account and project
- Stripe account (test mode for development)
- OpenRouter API key

### Environment Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your credentials:
   ```env
   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key

   # Stripe
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...

   # OpenRouter
   OPENROUTER_API_KEY=your_openrouter_key

   # App Config
   SECRET_KEY=your_secret_key_for_jwt
   ENVIRONMENT=development
   ```

### Database Setup

The app will automatically create the required tables on first run. Required tables:
- `users` - User accounts and credit balances
- `mocks` - Mock exam definitions
- `attempts` - User exam attempts and scores
- `tickets` - Support tickets

### Running the Application

#### Development Mode

1. Start the FastAPI backend:
   ```bash
   uvicorn api:app --reload --port 8000
   ```

2. In a new terminal, start the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

3. Access the application at `http://localhost:8501`

#### Production Deployment

For production, consider:
- Deploy FastAPI backend to Heroku/Render/Railway
- Deploy Streamlit frontend to Streamlit Cloud
- Set up proper domain and SSL
- Configure Stripe webhook endpoint

## Project Structure

```
/
├── streamlit_app.py      # Main Streamlit application
├── api.py               # FastAPI backend server
├── config.py            # Configuration and environment variables
├── db.py                # Database connection and operations
├── models.py            # Pydantic models and schemas
├── stripe_utils.py      # Stripe payment integration
├── openrouter_utils.py  # OpenRouter AI integration
├── pdf_utils.py         # PDF generation utilities
├── admin_utils.py       # Admin dashboard utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage

### For Students
1. Register/login to your account
2. Purchase credits via Stripe
3. Browse available mock exams
4. Take exams (1 credit per attempt)
5. View results and download PDFs
6. Unlock explanations for additional insights

### For Administrators
1. Login with admin credentials
2. Access admin dashboard
3. Create/edit mock exams
4. Generate AI-powered explanations
5. Manage user accounts and support tickets

## API Endpoints

- `POST /api/stripe/create-checkout` - Create Stripe checkout session
- `POST /api/stripe/webhook` - Handle Stripe webhooks
- `POST /api/mocks/start-attempt` - Start a mock exam attempt
- `POST /api/mocks/submit` - Submit exam answers
- `GET /api/mocks/{mock_id}/pdf` - Download exam PDF
- `POST /api/openrouter/generate-explanation` - Generate AI explanations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and support, please create a ticket through the application or contact the administrator.