# MockExamify Quick Start Guide

## Demo Mode (No Setup Required)

To try MockExamify immediately without any external services:

```bash
python demo.py
```

This will start both the backend and frontend with mock data. Access the app at http://localhost:8501

**Demo Accounts:**
- Admin: `admin@demo.com` / `admin123`
- User: `user@demo.com` / `user123`

## Full Production Setup

### 1. Prerequisites

- Python 3.8+
- Supabase account (free tier available)
- Stripe account (test mode for development)
- OpenRouter API key (optional, for AI features)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Fill in your credentials:

```env
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Stripe (Required for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OpenRouter (Optional, for AI features)
OPENROUTER_API_KEY=sk-or-...

# Security
SECRET_KEY=your_random_secret_key_here
```

### 4. Database Setup

Initialize the database with sample data:

```bash
python init_db.py
```

This creates:
- Database tables
- Sample mock exams
- Admin user: `admin@example.com` / `admin123`

### 5. Run the Application

```bash
python start.py
```

Access the app at:
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

## Features Overview

### For Users
- 📝 Take interactive mock exams
- 💳 Purchase credits via Stripe
- 📄 Download PDF results
- 🤖 AI-powered explanations (optional)

### For Admins
- 🛠️ Create and manage mock exams
- 📊 View user attempts and analytics
- 🎯 Configure credit packages
- 🤖 Generate AI content

## Testing

Run the setup verification:

```bash
python test_setup.py
```

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set environment variables
4. Deploy!

### Railway/Render
1. Deploy backend API separately
2. Update `API_BASE_URL` in frontend
3. Deploy frontend to Streamlit Cloud

## Troubleshooting

### Database Issues
- Verify Supabase URL and key
- Check project is active
- Run `python init_db.py` again

### Payment Issues
- Test with Stripe test cards
- Verify webhook endpoint
- Check Stripe dashboard logs

### PDF Generation Issues
- Install system dependencies for WeasyPrint
- Check file permissions

Need help? Check the logs or run `python test_setup.py` for diagnostics.