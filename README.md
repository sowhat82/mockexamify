# MockExamify - Interactive Mock Exam Platform 🎯 <!-- color-change-test -->

A comprehensive full-stack Python application for selling and hosting interactive mock exams with credit system, payments, and AI integration.

## ✨ Features

### Core Functionality
- 🎯 **Interactive Mock Exams** - Multiple-choice exams with timer and progress tracking
- 💳 **Credit System** - Flexible pay-per-exam model with Stripe integration
- 🤖 **AI-Powered Explanations** - OpenRouter integration for detailed answer explanations
- 📄 **PDF Reports** - Comprehensive exam reports with performance analysis
- 👥 **User Management** - Secure authentication with role-based access control
- 📊 **Analytics Dashboard** - User progress tracking and performance insights

### Admin Features
- 🛠️ **Admin Dashboard** - Complete platform management interface
- 📈 **Analytics & Insights** - User statistics, performance metrics, and growth tracking
- 📝 **Mock Exam Management** - Create, edit, and manage exam content
- 🎫 **Support System** - Comprehensive ticket management system
- 🤖 **AI Content Generation** - Automated explanation generation for exam questions

### User Experience
- 🎨 **Modern UI/UX** - Clean, responsive design with intuitive navigation
- 📱 **Mobile Friendly** - Optimized for all device sizes
- 🔄 **Auto-Save** - Progress automatically saved during exams
- 📁 **Download Reports** - PDF exam reports with detailed analysis
- 💬 **Support Center** - Built-in help desk and FAQ system

## 🚀 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Interactive web interface |
| **Backend** | FastAPI | RESTful API and business logic |
| **Database** | Supabase | PostgreSQL with built-in auth |
| **Payments** | Stripe | Secure credit card processing |
| **AI** | OpenRouter | GPT-4 powered explanations |
| **PDF** | ReportLab | Professional report generation |
| **Charts** | Plotly | Interactive data visualization |

## 📋 Prerequisites

- **Python 3.8+** (Recommended: Python 3.11+)
- **Supabase Account** - Database and authentication
- **Stripe Account** - Payment processing (test mode for development)
- **OpenRouter API Key** - AI explanation generation
- **Node.js** (Optional) - For advanced development tools

## ⚙️ Installation & Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/mockexamify.git
cd mockexamify

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Database & Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Payment Processing
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_1...

# AI Integration
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini

# Application Security
SECRET_KEY=your_jwt_secret_key_here
ENVIRONMENT=development

# Optional: PDF Generation Settings
PDF_TEMP_DIR=./temp_pdfs
MAX_PDF_SIZE_MB=10
```

### 3. Database Setup

The application automatically creates required tables on first run:

```sql
-- Tables created automatically:
-- users (id, email, password_hash, credits_balance, role, created_at)
-- mocks (id, title, description, questions_json, created_by, is_active)
-- attempts (id, user_id, mock_id, score, answers_json, completed_at)
-- tickets (id, user_id, subject, description, status, created_at)
```

### 4. Initial Data (Optional)

```bash
# Create admin user
python create_admin_user.py

# Run initial setup tests
python test_setup.py
```

## 🏃‍♂️ Running the Application

### Development Mode

#### Option 1: Using the Start Script (Recommended)
```bash
python start.py
```
This automatically starts both FastAPI backend and Streamlit frontend.

#### Option 2: Manual Startup
```bash
# Terminal 1: Start FastAPI backend
uvicorn api:app --reload --port 8000

# Terminal 2: Start Streamlit frontend
streamlit run streamlit_app.py --server.port 8501
```

Access the application:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Production Deployment

#### Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Add environment variables in Streamlit settings
4. Deploy with auto-updates enabled

#### Docker Deployment
```dockerfile
# Dockerfile (create in project root)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
```

```bash
# Build and run
docker build -t mockexamify .
docker run -p 8501:8501 --env-file .env mockexamify
```

#### Railway/Heroku Deployment
1. Create `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
   ```
2. Set environment variables in platform dashboard
3. Deploy from GitHub repository

## 📁 Project Structure

```
mockexamify/
├── 📱 Frontend (Streamlit)
│   ├── streamlit_app.py           # Main application entry point
│   └── pages/                     # Page components
│       ├── dashboard.py           # User dashboard
│       ├── exam.py                # Exam interface
│       ├── purchase_credits.py    # Payment flow
│       ├── past_attempts.py       # Exam history
│       ├── contact_support.py     # Support system
│       ├── admin_dashboard.py     # Admin analytics
│       ├── admin_upload.py        # Exam creation
│       └── admin_manage.py        # Content management
│
├── ⚙️ Backend (FastAPI)
│   ├── api.py                     # REST API endpoints
│   ├── db.py                      # Database operations
│   ├── models.py                  # Data models
│   ├── auth_utils.py              # Authentication
│   └── admin_utils.py             # Admin operations
│
├── 🔌 Integrations
│   ├── stripe_utils.py            # Payment processing
│   ├── openrouter_utils.py        # AI explanations
│   └── pdf_utils.py               # Report generation
│
├── ⚙️ Configuration
│   ├── config.py                  # App configuration
│   ├── requirements.txt           # Dependencies
│   └── .env                       # Environment variables
│
├── 📊 Data & Storage
│   ├── temp_pdfs/                 # Generated reports
│   └── templates/                 # Email/PDF templates
│
└── 🚀 Deployment
    ├── start.py                   # Development launcher
    ├── Procfile                   # Heroku deployment
    └── README.md                  # This file
```

## 🎮 Usage Guide

### For Students

1. **Registration & Login**
   - Create account with email verification
   - Secure password requirements enforced

2. **Purchase Credits**
   - Multiple package options (5, 20, 50, 100 credits)
   - Secure Stripe checkout process
   - Credits never expire

3. **Take Exams**
   - Browse available mock exams by category
   - View difficulty level and credit cost
   - Timer-based exams with auto-save

4. **View Results**
   - Immediate score feedback
   - Detailed question-by-question analysis
   - Download comprehensive PDF reports

5. **Get Support**
   - Built-in help center with FAQ
   - Submit support tickets with tracking
   - Email notifications for updates

### For Administrators

1. **Dashboard Analytics**
   - User growth and engagement metrics
   - Revenue and credit usage tracking
   - Performance analytics with charts

2. **Mock Exam Management**
   - Create exams with JSON import/export
   - AI-powered explanation generation
   - Bulk edit and organization tools

3. **User Management**
   - View user accounts and activity
   - Credit balance adjustments
   - Account status management

4. **Support System**
   - Ticket queue management
   - Response templates and automation
   - User communication tracking

## 🛠️ API Documentation

### Authentication Endpoints
```http
POST /api/auth/login          # User login
POST /api/auth/register       # User registration  
POST /api/auth/refresh        # Token refresh
POST /api/auth/logout         # User logout
```

### Mock Exam Endpoints
```http
GET /api/mocks                # List available exams
GET /api/mocks/{id}          # Get exam details
POST /api/mocks/start        # Start exam attempt
POST /api/mocks/submit       # Submit exam answers
GET /api/mocks/{id}/pdf      # Download exam PDF
```

### Payment Endpoints
```http
POST /api/payments/checkout   # Create Stripe session
POST /api/payments/webhook    # Stripe webhook handler
GET /api/payments/history     # Payment history
```

### Admin Endpoints
```http
GET /api/admin/analytics     # Platform analytics
POST /api/admin/mocks        # Create mock exam
PUT /api/admin/mocks/{id}    # Update mock exam
DELETE /api/admin/mocks/{id} # Delete mock exam
GET /api/admin/users         # User management
```

## 🧪 Testing

### Run Test Suite
```bash
# Basic functionality tests
python test_setup.py

# Database connectivity
python test_db_connection.py

# API endpoint tests
python -m pytest tests/ -v

# Load testing (optional)
python -m locust -f tests/load_test.py
```

### Manual Testing Checklist

#### Core Functionality
- [ ] User registration and login
- [ ] Credit purchase flow
- [ ] Exam taking experience
- [ ] PDF report generation
- [ ] Support ticket system

#### Admin Features
- [ ] Admin dashboard analytics
- [ ] Mock exam creation/editing
- [ ] User management
- [ ] Support ticket handling

#### Integration Tests
- [ ] Stripe payment processing
- [ ] OpenRouter AI explanations
- [ ] PDF generation service
- [ ] Email notifications

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check Supabase credentials
python -c "import db; print(db.get_db_status())"
```

**Payment Processing Issues**
```bash
# Verify Stripe configuration
python -c "import stripe_utils; stripe_utils.test_connection()"
```

**AI Explanation Failures**
```bash
# Test OpenRouter API
python -c "import openrouter_utils; openrouter_utils.test_api()"
```

**PDF Generation Problems**
```bash
# Check ReportLab installation
python -c "import reportlab; print('ReportLab version:', reportlab.Version)"
```

### Performance Optimization

1. **Database Optimization**
   - Enable connection pooling
   - Add database indexes for frequent queries
   - Use database caching for static content

2. **API Performance**
   - Implement Redis caching
   - Add request rate limiting
   - Use async/await for I/O operations

3. **Frontend Optimization**
   - Enable Streamlit caching
   - Optimize image and asset loading
   - Implement lazy loading for large datasets

## 🔐 Security Considerations

### Authentication & Authorization
- JWT tokens with secure secret keys
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Session timeout and rotation

### Data Protection
- Environment variable security
- Database connection encryption
- HTTPS enforcement in production
- Input validation and sanitization

### Payment Security
- PCI compliance through Stripe
- Webhook signature verification
- Secure API key management
- Transaction logging and monitoring

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with proper testing
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Submit pull request

### Code Standards
- Follow PEP 8 for Python code
- Add docstrings for all functions
- Include type hints where appropriate
- Write tests for new features
- Update documentation as needed

### Reporting Issues
- Use GitHub Issues for bug reports
- Include environment details
- Provide reproduction steps
- Add screenshots if applicable

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** - Excellent framework for rapid web app development
- **Supabase** - Reliable backend-as-a-service platform
- **Stripe** - Secure and developer-friendly payment processing
- **OpenRouter** - Access to state-of-the-art AI models
- **ReportLab** - Professional PDF generation capabilities

## 📞 Support & Contact

- **Documentation**: [GitHub Wiki](https://github.com/yourusername/mockexamify/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/mockexamify/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mockexamify/discussions)
- **Email**: support@mockexamify.com

---

**Built with ❤️ by the MockExamify Team**

*Making exam preparation accessible, interactive, and intelligent.*
