"""
Enhanced PDF generation utilities for MockExamify
Comprehensive PDF generation with download links, storage management, and enhanced features
"""
import os
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from io import BytesIO
import base64
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedPDFGenerator:
    """Enhanced PDF generator with advanced features"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.temp_dir = os.path.join(os.getcwd(), "temp_pdfs")
        self._ensure_temp_directory()
    
    def _ensure_temp_directory(self):
        """Ensure temp directory exists"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def _setup_custom_styles(self):
        """Setup enhanced paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            spaceBefore=15,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Question style
        self.question_style = ParagraphStyle(
            'Question',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            leftIndent=0,
            fontName='Helvetica-Bold',
            borderColor=colors.lightblue,
            borderWidth=1,
            borderPadding=8,
            backColor=colors.aliceblue
        )
        
        # Choice style
        self.choice_style = ParagraphStyle(
            'Choice',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25
        )
        
        # Correct answer style
        self.correct_style = ParagraphStyle(
            'CorrectAnswer',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )
        
        # Wrong answer style
        self.wrong_style = ParagraphStyle(
            'WrongAnswer',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=25,
            textColor=colors.darkred,
            fontName='Helvetica-Bold'
        )
        
        # Explanation style
        self.explanation_style = ParagraphStyle(
            'Explanation',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            spaceBefore=6,
            leftIndent=25,
            rightIndent=10,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=10,
            backColor=colors.whitesmoke
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    
    async def generate_exam_results_pdf(
        self, 
        attempt_data: Dict[str, Any],
        mock_data: Dict[str, Any],
        user_data: Dict[str, Any],
        include_explanations: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate comprehensive exam results PDF
        Returns: (file_path, download_url)
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exam_results_{attempt_data['id']}_{timestamp}.pdf"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=50
            )
            
            story = []
            
            # Cover page
            story.extend(self._create_results_cover_page(attempt_data, mock_data, user_data))
            
            # Performance summary
            story.append(PageBreak())
            story.extend(self._create_performance_summary(attempt_data, mock_data))
            
            # Question-by-question analysis
            story.append(PageBreak())
            story.extend(self._create_detailed_analysis(attempt_data, mock_data, include_explanations))
            
            # Study recommendations
            story.append(PageBreak())
            story.extend(self._create_study_recommendations(attempt_data, mock_data))
            
            # Build PDF
            doc.build(story)
            
            # Generate download URL (for cloud storage or direct access)
            download_url = self._generate_download_url(filename)
            
            logger.info(f"Generated exam results PDF: {filepath}")
            return filepath, download_url
            
        except Exception as e:
            logger.error(f"Error generating exam results PDF: {e}")
            return None, None
    
    def _create_results_cover_page(self, attempt_data: Dict, mock_data: Dict, user_data: Dict) -> List:
        """Create enhanced cover page for results"""
        story = []
        
        # Header
        story.append(Paragraph("MockExamify", self.header_style))
        story.append(Spacer(1, 20))
        
        # Main title
        story.append(Paragraph("Exam Results Report", self.title_style))
        story.append(Spacer(1, 30))
        
        # Exam information
        exam_info = f"""
        <b>Exam:</b> {mock_data.get('title', 'Unknown Exam')}<br/>
        <b>Category:</b> {mock_data.get('category', 'General')}<br/>
        <b>Student:</b> {user_data.get('email', 'Unknown')}<br/>
        <b>Completion Date:</b> {attempt_data.get('completed_at', 'Unknown')}<br/>
        <b>Time Taken:</b> {self._format_time_taken(attempt_data.get('time_taken'))}
        """
        story.append(Paragraph(exam_info, self.styles['Normal']))
        story.append(Spacer(1, 40))
        
        # Score display
        score = attempt_data.get('score', 0)
        score_color = self._get_score_color(score)
        
        score_table_data = [
            ['Final Score', f"{score:.1f}%"],
            ['Questions Correct', f"{attempt_data.get('correct_answers', 0)} / {attempt_data.get('total_questions', 0)}"],
            ['Grade', self._get_letter_grade(score)]
        ]
        
        score_table = Table(score_table_data, colWidths=[2*inch, 2*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), score_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.white),
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 40))
        
        # Performance indicator
        performance_msg = self._get_performance_message(score)
        story.append(Paragraph(f"<b>Performance:</b> {performance_msg}", self.styles['Normal']))
        
        return story
    
    def _create_performance_summary(self, attempt_data: Dict, mock_data: Dict) -> List:
        """Create performance summary with charts"""
        story = []
        
        story.append(Paragraph("Performance Summary", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        # Basic statistics
        correct = attempt_data.get('correct_answers', 0)
        total = attempt_data.get('total_questions', 0)
        incorrect = total - correct
        
        stats_data = [
            ['Metric', 'Value', 'Percentage'],
            ['Correct Answers', str(correct), f"{(correct/total*100):.1f}%" if total > 0 else "0%"],
            ['Incorrect Answers', str(incorrect), f"{(incorrect/total*100):.1f}%" if total > 0 else "0%"],
            ['Total Questions', str(total), "100%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 30))
        
        # Time analysis
        time_taken = attempt_data.get('time_taken')
        if time_taken:
            time_limit = mock_data.get('time_limit_minutes', 60) * 60  # Convert to seconds
            time_efficiency = (time_taken / time_limit * 100) if time_limit > 0 else 0
            
            time_info = f"""
            <b>Time Management:</b><br/>
            • Time taken: {self._format_time_taken(time_taken)}<br/>
            • Time limit: {mock_data.get('time_limit_minutes', 60)} minutes<br/>
            • Efficiency: {time_efficiency:.1f}% of allowed time used
            """
            story.append(Paragraph(time_info, self.styles['Normal']))
        
        return story
    
    def _create_detailed_analysis(self, attempt_data: Dict, mock_data: Dict, include_explanations: bool) -> List:
        """Create detailed question-by-question analysis"""
        story = []
        
        story.append(Paragraph("Detailed Question Analysis", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        # Get questions and user answers
        questions = mock_data.get('questions_json', [])
        user_answers = attempt_data.get('user_answers', {})
        detailed_results = attempt_data.get('detailed_results', [])
        
        for i, question_data in enumerate(detailed_results):
            question_num = i + 1
            is_correct = question_data.get('is_correct', False)
            user_answer_idx = question_data.get('user_answer')
            correct_idx = question_data.get('correct_answer')
            choices = question_data.get('choices', [])
            
            # Question header
            status_icon = "✅" if is_correct else "❌"
            question_header = f"{status_icon} Question {question_num}"
            story.append(Paragraph(question_header, self.question_style))
            
            # Question text
            question_text = question_data.get('question', '')
            story.append(Paragraph(f"<b>Q:</b> {question_text}", self.styles['Normal']))
            story.append(Spacer(1, 8))
            
            # Answer choices with highlighting
            for choice_idx, choice_text in enumerate(choices):
                choice_letter = chr(65 + choice_idx)
                
                if choice_idx == correct_idx:
                    # Correct answer
                    style = self.correct_style
                    prefix = f"✓ {choice_letter}."
                elif choice_idx == user_answer_idx and not is_correct:
                    # User's wrong answer
                    style = self.wrong_style
                    prefix = f"✗ {choice_letter}."
                else:
                    # Other choices
                    style = self.choice_style
                    prefix = f"{choice_letter}."
                
                story.append(Paragraph(f"{prefix} {choice_text}", style))
            
            # Show user's selection and correct answer
            if user_answer_idx is not None:
                user_choice = chr(65 + user_answer_idx)
                correct_choice = chr(65 + correct_idx)
                
                answer_summary = f"<b>Your Answer:</b> {user_choice} | <b>Correct Answer:</b> {correct_choice}"
                story.append(Spacer(1, 8))
                story.append(Paragraph(answer_summary, self.styles['Normal']))
            
            # Add explanation if available and requested
            if include_explanations:
                explanation = self._get_question_explanation(question_data, questions, i)
                if explanation:
                    story.append(Spacer(1, 8))
                    story.append(Paragraph("<b>Explanation:</b>", self.styles['Normal']))
                    story.append(Paragraph(explanation, self.explanation_style))
            
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_study_recommendations(self, attempt_data: Dict, mock_data: Dict) -> List:
        """Create personalized study recommendations"""
        story = []
        
        story.append(Paragraph("Study Recommendations", self.subtitle_style))
        story.append(Spacer(1, 20))
        
        score = attempt_data.get('score', 0)
        
        # General recommendations based on score
        if score >= 90:
            recommendations = [
                "Excellent performance! You have mastered this topic.",
                "Consider taking more advanced exams in this subject area.",
                "Review any questions you got wrong to achieve perfect scores.",
                "Share your knowledge by helping others study."
            ]
        elif score >= 80:
            recommendations = [
                "Good performance! You have a strong understanding of the material.",
                "Focus on the topics where you made mistakes.",
                "Take additional practice exams to reinforce your knowledge.",
                "Consider studying more advanced concepts in this area."
            ]
        elif score >= 70:
            recommendations = [
                "Fair performance. You understand the basics but need more practice.",
                "Review the questions you got wrong and understand why.",
                "Focus on weak areas identified in your detailed analysis.",
                "Take more practice exams before the real test."
            ]
        elif score >= 60:
            recommendations = [
                "Below average performance. Significant study is needed.",
                "Review fundamental concepts in this subject area.",
                "Consider getting additional help or tutoring.",
                "Practice regularly with similar exams."
            ]
        else:
            recommendations = [
                "Poor performance. Extensive study and review required.",
                "Start with basic concepts and build up gradually.",
                "Consider taking a preparatory course.",
                "Seek help from instructors or study groups."
            ]
        
        # Add topic-specific recommendations based on wrong answers
        wrong_topics = self._identify_weak_topics(attempt_data)
        if wrong_topics:
            recommendations.append(f"Focus particularly on: {', '.join(wrong_topics)}")
        
        # Format recommendations
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 20))
        
        # Study plan suggestion
        study_plan = f"""
        <b>Suggested Study Plan:</b><br/>
        • Spend at least {max(1, (100-score)//10)} hours reviewing material<br/>
        • Take {max(1, (100-score)//20)} additional practice exams<br/>
        • Focus {max(30, (100-score))}% of study time on weak areas<br/>
        • Review this exam again in 1 week
        """
        story.append(Paragraph(study_plan, self.styles['Normal']))
        
        return story
    
    def _format_time_taken(self, seconds: Optional[int]) -> str:
        """Format time taken in human-readable format"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _get_score_color(self, score: float) -> colors.Color:
        """Get color based on score"""
        if score >= 90:
            return colors.darkgreen
        elif score >= 80:
            return colors.green
        elif score >= 70:
            return colors.orange
        elif score >= 60:
            return colors.darkorange
        else:
            return colors.red
    
    def _get_letter_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 97:
            return "A+"
        elif score >= 93:
            return "A"
        elif score >= 90:
            return "A-"
        elif score >= 87:
            return "B+"
        elif score >= 83:
            return "B"
        elif score >= 80:
            return "B-"
        elif score >= 77:
            return "C+"
        elif score >= 73:
            return "C"
        elif score >= 70:
            return "C-"
        elif score >= 67:
            return "D+"
        elif score >= 65:
            return "D"
        else:
            return "F"
    
    def _get_performance_message(self, score: float) -> str:
        """Get performance message based on score"""
        if score >= 90:
            return "Outstanding! You demonstrated excellent mastery of the material."
        elif score >= 80:
            return "Good work! You have a solid understanding with room for minor improvements."
        elif score >= 70:
            return "Satisfactory performance with several areas needing attention."
        elif score >= 60:
            return "Below expectations. Significant study and practice needed."
        else:
            return "Unsatisfactory. Comprehensive review and additional preparation required."
    
    def _get_question_explanation(self, question_data: Dict, questions: List, index: int) -> str:
        """Get explanation for a question"""
        # Try to get from detailed results first
        if 'explanation' in question_data:
            return question_data['explanation']
        
        # Fallback to original question data
        if index < len(questions):
            question = questions[index]
            return question.get('explanation_template', question.get('explanation', ''))
        
        return ""
    
    def _identify_weak_topics(self, attempt_data: Dict) -> List[str]:
        """Identify topics where user performed poorly"""
        # This is a simplified implementation
        # In a real system, you'd analyze question topics/tags
        detailed_results = attempt_data.get('detailed_results', [])
        wrong_questions = [r for r in detailed_results if not r.get('is_correct', True)]
        
        # For now, return generic recommendations
        if len(wrong_questions) > len(detailed_results) * 0.5:
            return ["fundamental concepts", "problem-solving techniques"]
        elif len(wrong_questions) > len(detailed_results) * 0.3:
            return ["specific topic areas covered in wrong answers"]
        else:
            return []
    
    def _generate_download_url(self, filename: str) -> str:
        """Generate download URL for the PDF"""
        # In a real implementation, this would upload to cloud storage
        # For now, return a local path
        return f"/download/pdf/{filename}"
    
    async def generate_answer_key_pdf(self, mock_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Generate answer key PDF for administrators"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"answer_key_{mock_data.get('id', 'unknown')}_{timestamp}.pdf"
            filepath = os.path.join(self.temp_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            
            # Title
            story.append(Paragraph(f"Answer Key: {mock_data.get('title', 'Unknown Exam')}", self.title_style))
            story.append(Spacer(1, 30))
            
            # Answer table
            questions = mock_data.get('questions_json', [])
            answer_data = [['Question #', 'Correct Answer', 'Choice Text']]
            
            for i, question in enumerate(questions):
                correct_idx = question.get('correct_index', 0)
                correct_letter = chr(65 + correct_idx)
                choices = question.get('choices', [])
                correct_text = choices[correct_idx] if correct_idx < len(choices) else "Unknown"
                
                answer_data.append([
                    str(i + 1),
                    correct_letter,
                    correct_text[:60] + "..." if len(correct_text) > 60 else correct_text
                ])
            
            table = Table(answer_data, colWidths=[1*inch, 1*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(table)
            doc.build(story)
            
            download_url = self._generate_download_url(filename)
            
            logger.info(f"Generated answer key PDF: {filepath}")
            return filepath, download_url
            
        except Exception as e:
            logger.error(f"Error generating answer key PDF: {e}")
            return None, None
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up old PDF files"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Removed old PDF file: {filename}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

# Global enhanced PDF generator instance
enhanced_pdf_generator = EnhancedPDFGenerator()

# Helper functions for easy access
async def generate_exam_results_pdf(attempt_data: Dict, mock_data: Dict, user_data: Dict, 
                                   include_explanations: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """Generate exam results PDF"""
    return await enhanced_pdf_generator.generate_exam_results_pdf(
        attempt_data, mock_data, user_data, include_explanations
    )

async def generate_answer_key_pdf(mock_data: Dict) -> Tuple[Optional[str], Optional[str]]:
    """Generate answer key PDF"""
    return await enhanced_pdf_generator.generate_answer_key_pdf(mock_data)

def cleanup_old_pdf_files(days_old: int = 7):
    """Clean up old PDF files"""
    enhanced_pdf_generator.cleanup_old_files(days_old)