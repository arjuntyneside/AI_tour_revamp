"""
Gemini AI Processing Module for Tour Document Extraction
Integrates with Google's Gemini AI for intelligent document processing
"""

import json
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.conf import settings
import os

# Configure logging
logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI library not installed. Install with: pip install google-generativeai")

class GeminiAIProcessor:
    """
    Handles AI processing using Google's Gemini AI for tour document extraction
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini AI processor
        
        Args:
            api_key: Gemini API key. If not provided, will try to get from settings
        """
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', None)
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in settings or pass api_key parameter.")
        
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library not installed. Install with: pip install google-generativeai")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Define the extraction prompt
        self.extraction_prompt = """
        You are an expert tour information extractor with high accuracy. Analyze the provided document and extract tour information in the following JSON format.
        
        CRITICAL: Extract ONLY the MAIN tour. If multiple tours are mentioned, focus on the primary tour and ignore extensions, add-ons, or optional tours.
        
        IMPORTANT: Set extraction_confidence to 0.9 or higher if you can extract the main tour details (title, destination, duration, description). Only use lower confidence if the document is unclear or contains no tour information.
        
        Return ONLY valid JSON in this exact format:
        {
            "extraction_confidence": 0.95,
            "extracted_tours": [
                {
                    "title": "Main Tour Title",
                    "destination": "Primary destination",
                    "duration_days": 3,
                    "pricing_type": "per_person",
                    "price_per_person": 299.99,
                    "price_per_group": 0,
                    "max_group_size": 15,
                    "description": "Detailed tour description",
                    "highlights": "Key highlights of the tour",
                    "included_services": "What's included in the tour",
                    "excluded_services": "What's not included",
                    "difficulty_level": "easy|moderate|challenging|expert",
                    "seasonal_demand": "high|medium|low|year_round",
                    "cost_per_person": 150.00,
                    "operational_costs": 500.00
                }
            ],
            "processing_notes": [
                "Successfully extracted main tour information",
                "Mention if extensions were found but ignored"
            ]
        }
        
        Guidelines:
        - Extract ONLY the main tour (ignore extensions/add-ons/optional tours)
        - Set extraction_confidence to 0.9+ if you can extract title, destination, duration, and description
        - If pricing is per group, set pricing_type to "per_group" and use price_per_group
        - If pricing is per person, set pricing_type to "per_person" and use price_per_person
        - Set difficulty_level based on tour type (city tours are usually easy, hiking tours are moderate/challenging)
        - Set seasonal_demand based on destination and tour type
        - Estimate cost_per_person as 60-70% of price_per_person for profit margin
        - Set operational_costs based on tour complexity (200-800 range)
        - If extensions are mentioned, note them in processing_notes but don't include in extracted_tours
        - Only use confidence < 0.9 if the document is unclear or contains no tour information
        
        Return only valid JSON, no additional text.
        """
    
    def extract_tour_information(self, document_content: str, file_type: str = "text") -> Dict[str, Any]:
        """
        Extract tour information from document content using Gemini AI
        
        Args:
            document_content: The content of the document to analyze
            file_type: Type of document (text, pdf, etc.)
            
        Returns:
            Dictionary containing extracted tour information
        """
        try:
            # Prepare the prompt with document content
            full_prompt = f"{self.extraction_prompt}\n\nDocument Content:\n{document_content}\n\nFile Type: {file_type}\n\nPlease extract the tour information:"
            
            # Generate response from Gemini with longer timeout
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.1,  # Lower temperature for more consistent results
                    'max_output_tokens': 4000,  # Allow longer responses
                }
            )
            
            # Parse the JSON response
            try:
                # Clean the response text - remove markdown code blocks if present
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove ```
                response_text = response_text.strip()
                
                extracted_data = json.loads(response_text)
                logger.info(f"Successfully extracted tour data with confidence: {extracted_data.get('extraction_confidence', 0)}")
                return extracted_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Raw response: {response.text}")
                
                # Try to extract JSON from markdown blocks
                try:
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1).strip()
                        extracted_data = json.loads(json_content)
                        logger.info(f"Successfully extracted tour data from markdown with confidence: {extracted_data.get('extraction_confidence', 0)}")
                        return extracted_data
                except Exception as markdown_parse_error:
                    logger.error(f"Failed to parse JSON from markdown: {markdown_parse_error}")
                
                # Return fallback data
                return self._create_fallback_data(document_content)
                
        except Exception as e:
            logger.error(f"Error in Gemini AI processing: {e}")
            return self._create_fallback_data(document_content)
    
    def _create_fallback_data(self, document_content: str) -> Dict[str, Any]:
        """
        Create fallback data when AI processing fails
        
        Args:
            document_content: Original document content
            
        Returns:
            Fallback tour data
        """
        return {
            "extraction_confidence": 0.0,
            "extracted_tours": [
                {
                    "title": None,
                    "destination": None,
                    "duration_days": None,
                    "pricing_type": "per_person",
                    "price_per_person": None,
                    "price_per_group": 0,
                    "max_group_size": None,
                    "description": None,
                    "highlights": None,
                    "included_services": None,
                    "excluded_services": None,
                    "difficulty_level": None,
                    "seasonal_demand": None,
                    "cost_per_person": None,
                    "operational_costs": 0,
                }
            ],
            "processing_notes": [
                "AI processing failed - unable to parse tour information",
                "Document content may be unclear or in unsupported format",
                "Please check if the document contains valid tour information"
            ]
        }
    
    def analyze_document_content(self, file_path: str) -> str:
        """
        Analyze document content based on file type
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content from the document
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                return self._read_text_file(file_path)
            elif file_extension == '.pdf':
                return self._read_pdf_file(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._read_word_file(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                return self._read_excel_file(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            logger.error(f"Error reading document content: {e}")
            return f"Error reading document: {str(e)}"
    
    def _read_text_file(self, file_path: str) -> str:
        """Read text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _read_pdf_file(self, file_path: str) -> str:
        """Read PDF file content"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            return "PDF processing requires PyPDF2. Install with: pip install PyPDF2"
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def _read_word_file(self, file_path: str) -> str:
        """Read Word document content"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            return "Word document processing requires python-docx. Install with: pip install python-docx"
        except Exception as e:
            return f"Error reading Word document: {str(e)}"
    
    def _read_excel_file(self, file_path: str) -> str:
        """Read Excel file content"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
        except ImportError:
            return "Excel processing is not available in this deployment. Please upload documents in PDF, Word, or text format."
        except Exception as e:
            return f"Error reading Excel file: {str(e)}"


def process_document_with_gemini(document_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process a document with Gemini AI
    
    Args:
        document_path: Path to the document file
        api_key: Gemini API key (optional)
        
    Returns:
        Extracted tour information
    """
    try:
        processor = GeminiAIProcessor(api_key)
        content = processor.analyze_document_content(document_path)
        return processor.extract_tour_information(content)
    except Exception as e:
        logger.error(f"Error processing document with Gemini: {e}")
        return {
            "extraction_confidence": 0.0,
            "extracted_tours": [],
            "processing_notes": [f"Processing failed: {str(e)}"]
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the processor
    test_content = """
    PARIS CITY TOUR
    Duration: 3 days
    Price: £299 per person
    Group size: Maximum 15 people
    
    Experience the magic of Paris with our comprehensive city tour. 
    Visit the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral.
    
    Included: Professional guide, transportation, entrance fees
    Not included: Meals, personal expenses
    """
    
    try:
        processor = GeminiAIProcessor("your-api-key-here")
        result = processor.extract_tour_information(test_content)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
