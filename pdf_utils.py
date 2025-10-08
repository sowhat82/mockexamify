"""
PDF generation utilities for MockExamify
"""
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
import config
from models import Mock, AttemptResponse, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFGenerator:
    """Handles PDF generation for mock exams"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Question style
        self.question_style = ParagraphStyle(
            'Question',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            leftIndent=0,
            fontName='Helvetica-Bold'
        )
        
        # Choice style
        self.choice_style = ParagraphStyle(
            'Choice',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20
        )
        
        # Explanation style
        self.explanation_style = ParagraphStyle(
            'Explanation',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            spaceBefore=6,
            leftIndent=20,
            borderColor=colors.lightgrey,
            borderWidth=1,
            borderPadding=10,
            backColor=colors.lightgrey
        )
        
        # Answer style
        self.answer_style = ParagraphStyle(
            'Answer',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )
    
    async def generate_exam_pdf(
        self, 
        mock: Mock, 
        attempt: Optional[AttemptResponse] = None, 
        user: Optional[User] = None,
        include_answers: bool = False,
        include_explanations: bool = False
    ) -> Optional[bytes]:
        """Generate PDF for exam with optional answers and explanations"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Title page
            story.extend(self._create_title_page(mock, user, attempt))
            
            # Questions
            for i, question in enumerate(mock.questions):
                story.extend(self._create_question_section(
                    question, 
                    i + 1, 
                    attempt,
                    include_answers,
                    include_explanations
                ))
            
            # Summary page if attempt provided
            if attempt:
                story.append(PageBreak())
                story.extend(self._create_summary_page(attempt, mock))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"Generated PDF for mock {mock.id}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None
    
    def _create_title_page(self, mock: Mock, user: Optional[User], attempt: Optional[AttemptResponse]) -> List:
        """Create the title page content"""
        story = []
        
        # Title
        story.append(Paragraph(mock.title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Description
        story.append(Paragraph(f"<b>Description:</b> {mock.description}", self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Exam details table
        exam_data = [
            ['Total Questions:', str(len(mock.questions))],
            ['Category:', mock.category or 'General'],
            ['Time Limit:', f"{mock.time_limit_minutes} minutes" if mock.time_limit_minutes else "No limit"],
        ]
        
        if attempt:
            exam_data.extend([
                ['Attempt Date:', attempt.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
                ['Score:', f"{attempt.score:.1f}% ({attempt.correct_answers}/{attempt.total_questions})"]
            ])
        
        if user:
            exam_data.append(['Student:', user.email])
        
        table = Table(exam_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Instructions
        instructions = """
        <b>Instructions:</b><br/>
        • Read each question carefully<br/>
        • Choose the best answer from the options provided<br/>
        • Only one answer is correct for each question<br/>
        • Review your answers before submission
        """
        story.append(Paragraph(instructions, self.styles['Normal']))
        story.append(PageBreak())
        
        return story
    
    def _create_question_section(
        self, 
        question: Dict[str, Any], 
        question_num: int, 
        attempt: Optional[AttemptResponse],
        include_answers: bool,
        include_explanations: bool
    ) -> List:
        """Create content for a single question"""
        story = []
        
        # Question text
        question_text = f"<b>Question {question_num}:</b> {question['question']}"
        story.append(Paragraph(question_text, self.question_style))
        
        # Choices
        for i, choice in enumerate(question['choices']):
            choice_letter = chr(65 + i)  # A, B, C, D
            choice_text = f"{choice_letter}. {choice}"
            
            # Highlight user's answer and correct answer if showing answers
            style = self.choice_style
            if include_answers:
                is_correct = i == question['correct_index']
                user_selected = attempt and len(attempt.user_answers) > question_num - 1 and attempt.user_answers[question_num - 1] == i
                
                if is_correct:
                    choice_text = f"<b>✓ {choice_text}</b>"  # Correct answer
                    style = self.answer_style
                elif user_selected and not is_correct:
                    choice_text = f"✗ {choice_text}"  # Wrong user selection
            
            story.append(Paragraph(choice_text, style))
        
        # Show explanation if requested and available
        if include_explanations and question.get('explanation_template'):
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Explanation:</b>", self.styles['Normal']))
            story.append(Paragraph(question['explanation_template'], self.explanation_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_summary_page(self, attempt: AttemptResponse, mock: Mock) -> List:
        """Create summary page with results"""
        story = []
        
        story.append(Paragraph("Exam Summary", self.title_style))
        story.append(Spacer(1, 20))
        
        # Results table
        results_data = [
            ['Total Questions:', str(attempt.total_questions)],
            ['Correct Answers:', str(attempt.correct_answers)],
            ['Incorrect Answers:', str(attempt.total_questions - attempt.correct_answers)],
            ['Score:', f"{attempt.score:.1f}%"],
            ['Completion Date:', attempt.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        table = Table(results_data, colWidths=[2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Performance analysis
        percentage = attempt.score
        if percentage >= 80:
            performance = "Excellent! You demonstrated strong understanding of the material."
        elif percentage >= 70:
            performance = "Good work! You have a solid grasp of most concepts."
        elif percentage >= 60:
            performance = "Fair performance. Consider reviewing the topics you missed."
        else:
            performance = "You may benefit from additional study before retaking this exam."
        
        story.append(Paragraph(f"<b>Performance Analysis:</b> {performance}", self.styles['Normal']))
        
        return story
    
    async def generate_answer_key_pdf(self, mock: Mock) -> Optional[bytes]:
        """Generate answer key PDF for administrators"""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            story = []
            
            # Title
            story.append(Paragraph(f"Answer Key: {mock.title}", self.title_style))
            story.append(Spacer(1, 30))
            
            # Answer key table
            answer_data = [['Question', 'Correct Answer', 'Choice Text']]
            
            for i, question in enumerate(mock.questions):
                correct_index = question['correct_index']
                correct_letter = chr(65 + correct_index)
                correct_text = question['choices'][correct_index]
                
                answer_data.append([
                    str(i + 1),
                    correct_letter,
                    correct_text[:50] + "..." if len(correct_text) > 50 else correct_text
                ])
            
            table = Table(answer_data, colWidths=[1*inch, 1*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            logger.info(f"Generated answer key PDF for mock {mock.id}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating answer key PDF: {e}")
            return None
    
    def save_pdf_to_file(self, pdf_content: bytes, filename: str) -> str:
        """Save PDF content to file and return path"""
        try:
            filepath = os.path.join(config.PDF_OUTPUT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            logger.info(f"Saved PDF to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving PDF to file: {e}")
            return ""


# Global PDF generator instance
pdf_generator = PDFGenerator()