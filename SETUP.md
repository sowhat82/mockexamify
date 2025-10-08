# MockExamify Setup Guide

## Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- Supabase account (free tier available)
- Stripe account (test mode for development)
- OpenRouter API key (optional, for AI features)

### 1. Environment Setup

1. **Clone/Download the project files**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file:**
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

### 2. Supabase Setup

1. **Create a new Supabase project:** https://supabase.com
2. **Get your credentials:** Project URL and anon key from Settings → API
3. **Create database tables:** Run the SQL from `init_db.py` in your Supabase SQL editor

#### Required SQL (Run in Supabase SQL Editor):

```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    credits_balance INTEGER DEFAULT 0,
    role VARCHAR(50) DEFAULT 'user',
    subscription_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mocks table
CREATE TABLE IF NOT EXISTS mocks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    questions_json JSONB NOT NULL,
    price_credits INTEGER DEFAULT 1,
    explanation_enabled BOOLEAN DEFAULT TRUE,
    time_limit_minutes INTEGER,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attempts table
CREATE TABLE IF NOT EXISTS attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) NOT NULL,
    mock_id UUID REFERENCES mocks(id) NOT NULL,
    user_answers_json JSONB NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    correct_answers INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    explanation_unlocked BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Support tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_mocks_category ON mocks(category);
CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
```

### 3. Stripe Setup

1. **Create Stripe account:** https://stripe.com
2. **Get test keys:** Dashboard → Developers → API keys
3. **Set up webhook endpoint:** Dashboard → Developers → Webhooks
   - Endpoint URL: `https://your-api-domain.com/api/stripe/webhook`
   - Events: `checkout.session.completed`

### 4. OpenRouter Setup (Optional)

1. **Get API key:** https://openrouter.ai
2. **Add to .env file**

### 5. Run the Application

#### Development Mode:

**Terminal 1 - Backend:**
```bash
uvicorn api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
streamlit run streamlit_app.py
```

#### Or use the deploy script:
```bash
python deploy.py
```

### 6. Initialize Sample Data

```bash
python init_db.py
```

This creates:
- Admin user: `admin@mockexamify.com` / `admin123`
- Sample user: `student@example.com` / `password123`
- Sample Python quiz with 5 questions

### 7. Access the Application

- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## Production Deployment

### Option 1: Streamlit Cloud + Railway/Render

1. **Deploy Backend:**
   - Push to GitHub
   - Deploy to Railway/Render/Heroku
   - Set environment variables
   - Update webhook URL in Stripe

2. **Deploy Frontend:**
   - Deploy to Streamlit Cloud
   - Update `API_BASE_URL` in config

### Option 2: Single Server Deployment

1. **Set up reverse proxy (nginx):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location /api/ {
           proxy_pass http://localhost:8000;
       }
       
       location / {
           proxy_pass http://localhost:8501;
       }
   }
   ```

2. **Use process manager (PM2/systemd):**
   ```bash
   pm2 start "uvicorn api:app --host 0.0.0.0 --port 8000" --name mockexamify-api
   pm2 start "streamlit run streamlit_app.py --server.port 8501" --name mockexamify-frontend
   ```

## Environment Variables Reference

### Required:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `STRIPE_SECRET_KEY` - Stripe secret key (sk_test_... for testing)
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key (pk_test_... for testing)
- `SECRET_KEY` - Random string for JWT signing

### Optional:
- `OPENROUTER_API_KEY` - For AI-powered features
- `STRIPE_WEBHOOK_SECRET` - For webhook verification
- `API_BASE_URL` - Backend URL (default: http://localhost:8000)

## Features Overview

### Student Features:
- ✅ User registration and authentication
- ✅ Credit-based exam system
- ✅ Interactive multiple-choice exams
- ✅ Real-time scoring and feedback
- ✅ PDF download of results
- ✅ Explanation unlock system
- ✅ Progress tracking
- ✅ Support ticket system

### Admin Features:
- ✅ Admin dashboard with analytics
- ✅ Mock exam management
- ✅ AI-powered question generation
- ✅ User management
- ✅ Support ticket management
- ✅ Revenue tracking

### Payment Features:
- ✅ Stripe integration
- ✅ Multiple credit pack options
- ✅ Secure webhook handling
- ✅ Automatic credit allocation

### AI Features (Optional):
- ✅ Automatic explanation generation
- ✅ Question variant creation
- ✅ Mock exam generation from topics

## Troubleshooting

### Common Issues:

1. **Import errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection failed:**
   - Check Supabase credentials
   - Ensure tables are created
   - Verify network access

3. **Stripe webhook errors:**
   - Check webhook URL configuration
   - Verify webhook secret
   - Test with Stripe CLI

4. **PDF generation errors:**
   - Install system dependencies for WeasyPrint
   - Check reportlab installation

5. **CORS errors:**
   - Update allowed origins in api.py
   - Check frontend URL configuration

### System Dependencies (Linux/Mac):

For PDF generation:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# macOS
brew install cairo pango gdk-pixbuf libffi
```

## Security Considerations

### Production Checklist:
- [ ] Change default admin password
- [ ] Use strong JWT secret key
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable Supabase RLS policies
- [ ] Use production Stripe keys
- [ ] Set up monitoring and logging
- [ ] Regular database backups
- [ ] Environment variable security

## Support

For issues and questions:
1. Check this setup guide
2. Review the troubleshooting section
3. Check GitHub issues
4. Create a support ticket in the app

## License

MIT License - See LICENSE file for details.