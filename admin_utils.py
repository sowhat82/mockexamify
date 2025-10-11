"""
Admin utilities for MockExamify
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import User, Mock, AttemptResponse, Ticket, DashboardStats, QuestionSchema
from db import db
from openrouter_utils import openrouter_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdminManager:
    """Handles admin-specific operations"""
    
    def __init__(self):
        pass
    
    def is_admin(self, user: User) -> bool:
        """Check if user has admin privileges"""
        return user.role == "admin"
    
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics for admin overview"""
        try:
            # Get total users
            users_result = db.client.table('users').select('id').execute()
            total_users = len(users_result.data) if users_result.data else 0
            
            # Get total mocks
            mocks_result = db.client.table('mocks').select('id').execute()
            total_mocks = len(mocks_result.data) if mocks_result.data else 0
            
            # Get total attempts
            attempts_result = db.client.table('attempts').select('id').execute()
            total_attempts = len(attempts_result.data) if attempts_result.data else 0
            
            # Get active users (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            active_users_result = db.client.table('attempts').select('user_id').gte('timestamp', thirty_days_ago).execute()
            unique_active_users = len(set(attempt['user_id'] for attempt in active_users_result.data)) if active_users_result.data else 0
            
            # Calculate estimated revenue (this would be more accurate with actual payment tracking)
            # For now, estimate based on attempts and average credit cost
            estimated_revenue = total_attempts * 299  # Assuming average $2.99 per attempt
            
            return DashboardStats(
                total_users=total_users,
                total_mocks=total_mocks,
                total_attempts=total_attempts,
                revenue_cents=estimated_revenue,
                active_users_last_30_days=unique_active_users
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return DashboardStats(
                total_users=0,
                total_mocks=0,
                total_attempts=0,
                revenue_cents=0,
                active_users_last_30_days=0
            )
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        try:
            result = db.client.table('users').select('*').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            users = []
            for user_data in result.data:
                users.append(User(
                    id=user_data['id'],
                    email=user_data['email'],
                    credits_balance=user_data['credits_balance'],
                    role=user_data['role'],
                    created_at=user_data['created_at']
                ))
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def update_user_role(self, user_id: str, new_role: str) -> bool:
        """Update user role (admin/user)"""
        try:
            if new_role not in ['admin', 'user']:
                return False
            
            result = db.client.table('users').update({
                'role': new_role
            }).eq('id', user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
    
    async def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed user information including attempts"""
        try:
            user = await db.get_user_by_id(user_id)
            if not user:
                return None
            
            attempts = await db.get_user_attempts(user_id)
            
            return {
                'user': user,
                'attempts': attempts,
                'total_attempts': len(attempts),
                'average_score': sum(a.score for a in attempts) / len(attempts) if attempts else 0,
                'last_activity': max(a.timestamp for a in attempts) if attempts else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return None
    
    async def create_mock_from_ai(self, topic: str, num_questions: int = 10, difficulty: str = "medium", creator_id: str = "") -> Optional[Mock]:
        """Create a mock exam using AI generation"""
        try:
            if not openrouter_manager.is_configured():
                logger.error("OpenRouter not configured")
                return None
            
            # Generate questions using AI
            questions = await openrouter_manager.generate_mock_from_topic(topic, num_questions, difficulty)
            
            if not questions:
                logger.error("Failed to generate questions")
                return None
            
            # Create mock in database
            mock_data = {
                'title': f"AI Generated: {topic}",
                'description': f"AI-generated mock exam on {topic} with {num_questions} questions at {difficulty} difficulty level.",
                'questions': [q.dict() for q in questions],
                'price_credits': 1,
                'explanation_enabled': True,
                'time_limit_minutes': num_questions * 2,  # 2 minutes per question
                'category': topic,
                'is_active': True
            }
            
            mock = await db.create_mock(mock_data, creator_id)
            
            if mock:
                logger.info(f"Created AI-generated mock: {mock.id}")
                return mock
            
        except Exception as e:
            logger.error(f"Error creating AI mock: {e}")
            return None
    
    async def enhance_mock_explanations(self, mock_id: str) -> bool:
        """Enhance a mock exam by generating AI explanations"""
        try:
            if not openrouter_manager.is_configured():
                logger.error("OpenRouter not configured")
                return False
            
            mock = await db.get_mock_by_id(mock_id)
            if not mock:
                return False
            
            updated_questions = []
            
            for question_data in mock.questions:
                question = QuestionSchema(**question_data)
                
                if not question.explanation_template:
                    correct_answer = question.choices[question.correct_index]
                    explanation = await openrouter_manager.generate_explanation(
                        question.question,
                        question.choices,
                        correct_answer
                    )
                    
                    if explanation:
                        question.explanation_template = explanation
                
                updated_questions.append(question.dict())
            
            # Update mock in database
            result = db.client.table('mocks').update({
                'questions_json': json.dumps(updated_questions)
            }).eq('id', mock_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error enhancing mock explanations: {e}")
            return False
    
    async def get_all_tickets(self, status: Optional[str] = None) -> List[Ticket]:
        """Get all support tickets"""
        try:
            query = db.client.table('tickets').select('*')
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).execute()
            
            tickets = []
            for ticket_data in result.data:
                tickets.append(Ticket(
                    id=ticket_data['id'],
                    user_id=ticket_data['user_id'],
                    subject=ticket_data['subject'],
                    message=ticket_data['message'],
                    status=ticket_data['status'],
                    created_at=ticket_data['created_at']
                ))
            
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting tickets: {e}")
            return []
    
    async def update_ticket_status(self, ticket_id: str, new_status: str) -> bool:
        """Update ticket status"""
        try:
            if new_status not in ['open', 'in_progress', 'closed']:
                return False
            
            result = db.client.table('tickets').update({
                'status': new_status
            }).eq('id', ticket_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating ticket status: {e}")
            return False
    
    async def delete_mock(self, mock_id: str) -> bool:
        """Delete a mock exam (soft delete by setting inactive)"""
        try:
            result = db.client.table('mocks').update({
                'is_active': False
            }).eq('id', mock_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deleting mock: {e}")
            return False
    
    async def get_mock_analytics(self, mock_id: str) -> Dict[str, Any]:
        """Get analytics for a specific mock"""
        try:
            # Get all attempts for this mock
            result = db.client.table('attempts').select('*').eq('mock_id', mock_id).execute()
            
            if not result.data:
                return {
                    'total_attempts': 0,
                    'average_score': 0,
                    'pass_rate': 0,
                    'completion_rate': 100,
                    'difficulty_rating': 'N/A'
                }
            
            attempts = result.data
            scores = [attempt['score'] for attempt in attempts]
            
            # Calculate metrics
            total_attempts = len(attempts)
            average_score = sum(scores) / total_attempts
            pass_rate = len([s for s in scores if s >= 70]) / total_attempts * 100  # 70% pass threshold
            
            # Determine difficulty rating based on average score
            if average_score >= 80:
                difficulty_rating = "Easy"
            elif average_score >= 60:
                difficulty_rating = "Medium"
            else:
                difficulty_rating = "Hard"
            
            return {
                'total_attempts': total_attempts,
                'average_score': round(average_score, 1),
                'pass_rate': round(pass_rate, 1),
                'completion_rate': 100,  # All recorded attempts are completed
                'difficulty_rating': difficulty_rating,
                'score_distribution': {
                    '90-100': len([s for s in scores if s >= 90]),
                    '80-89': len([s for s in scores if 80 <= s < 90]),
                    '70-79': len([s for s in scores if 70 <= s < 80]),
                    '60-69': len([s for s in scores if 60 <= s < 70]),
                    'Below 60': len([s for s in scores if s < 60])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting mock analytics: {e}")
            return {}
    
    async def bulk_update_user_credits(self, user_credits: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk update user credits"""
        try:
            success_count = 0
            error_count = 0
            
            for update in user_credits:
                user_id = update.get('user_id')
                credits = update.get('credits', 0)
                
                if await db.update_user_credits(user_id, credits):
                    success_count += 1
                else:
                    error_count += 1
            
            return {
                'success_count': success_count,
                'error_count': error_count
            }
            
        except Exception as e:
            logger.error(f"Error in bulk credit update: {e}")
            return {'success_count': 0, 'error_count': len(user_credits)}


# Global admin manager instance
admin_manager = AdminManager()