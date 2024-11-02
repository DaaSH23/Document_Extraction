import redis
import json
import base64
import pytesseract
from datetime import datetime 
import cv2
import numpy as np
from PIL import Image
from PIL import ImageEnhance
from passporteye import read_mrz
import io
import re
import hashlib
from typing import Dict, Optional, Any, Tuple

# Class to handle doc info extraction with OCR capture and Redis integration
class DocumentProcessor:

    def __init__(self, redis_client, tesseract_cmd: str = None):
        
        self.redis_client = redis_client
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
        # Field extractors mapping
        self.field_extractors = {
            'Surname': self.extract_surname,
            'GivenName': self.extract_GivenName,
            'PassportNo': self.extract_PassportNumber,
            'Nationality': self.extract_Nationality,
            'Sex': self.extract_Sex,
            'DateOfBirth': self.extract_DOB,
            'PlaceOfBirth': self.extract_POB,
            'PlaceOfIssue': self.extract_POI,
            'IssueDate': self.extract_IssueDate,
            'ExpiryDate': self.extract_ExpiryDate
        }
        
        
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        
        # Enchance Contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Convert back to PIL Image
        return image
    
    def process_document(self, base64_image: str) -> Dict[str, Any]:
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(processed_image)
            print(extracted_text)
            
            # Try to read MRZ if available
            mrz_data = None
            try:
                mrz_data = read_mrz(io.BytesIO(image_data))
            except Exception:
                pass
            
            # Extract all fields
            extracted_data = {}
            for field, extractor in self.field_extractors.items():
                extracted_data[field] = extractor(extracted_text)
            
            # Add metadata
            extracted_data['metadata'] = {
                'processing_timestamp': datetime.now().isoformat(),
                'mrz_detected': mrz_data is not None,
                'text_hash': hashlib.sha256(extracted_text.encode()).hexdigest()
            }
            # print(extracted_data)
            return extracted_data
        
        except Exception as e:
            return {
                'error': str(e),
                'metadata': {
                    'processing_timestamp': datetime.now().isoformat(),
                    'status': 'failed'
                }
            }
            
    # Field extraction methods (your existing extraction methods)
    def extract_surname(self, text: str) -> Optional[str]:
        patterns = [
            r"Surname\s*([A-Z]+)",
            r"^([A-Z]+)\s*(?=\/|\n|$)",
            r"^([A-Z]+)(?=\s+[A-Za-z])",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        mrz_match = re.search(r"P<IND([A-Z]+)<<", text)
        if mrz_match:
            return mrz_match.group(1).strip()
        
        return None
    
    # function for extracting Given Name from regex
    def extract_GivenName(self, text: str) -> Optional[str]:
        patterns = [
            r"Given Name\(s\)\s*\/?\s*([A-Z\s]+)",
            r"([A-Z]+\s+[A-Z]+)(?=\s*\/|\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).split('\n', 1)[0].strip()
            
        mrz_match = re.search(r"P<IND[A-Z]+<<([A-Z]+)<<", text)
        if mrz_match:
            return mrz_match.group(1).strip()
        
        return None
    

    # function for extraction of document Number
    def extract_PassportNumber(self, text: str) -> Optional[str]:
        patterns = [
            r'(?:Passport No.|No.)?\s*([A-Z]\s*\d{7})',
            r'P<IND.*\n.*?(\d{7})',  
            r'[A-Z]\d{7}', 
            r'[A-Z][\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                try:
                    number = match.group(1)
                except (IndexError, AttributeError):
                    number = match.group(0)
                
                # Clean the extracted number (remove spaces and normalize)
                cleaned_number = ''.join(number.strip().split())
                
                # Validate the format (letter followed by 7 digits)
                if re.match(r'^[A-Z]\d{7}$', cleaned_number):
                    return cleaned_number
        
        return None

    # function for extracting nationality from regex
    def extract_Nationality(self, text: str) -> Optional[str]:
        patterns = [
            r'(?:Nationality|ARGH)\s*[:\/]?\s*([A-Z]+)',
            r'\bIND\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                try:
                    return match.group(1).strip()
                except:
                    return match.group(0).strip()
        return None


    # function for extracting POB from regex
    def extract_POB(self, text: str) -> Optional[str]:
        patterns = [
            r'~([A-Za-z\s,\.]+?),([A-Za-z\s]+)(?=\n|$)',
            r'(?i)Place of Birth\s*[:\/]?\s*([A-Za-z\s,\.]+?)(?=\n|$)',
            r'(?i)Birth\n\s*([A-Za-z\s,\.]+?)(?=\n|$)',
            r'~([A-Za-z\s,\.]+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                try:
                    # Try to get both groups for two-part location
                    if ',' in pattern:
                        return f"{match.group(1)},{match.group(2)}".strip()
                    # Otherwise just return the single group
                    return match.group(1).strip()
                except IndexError:
                    # If second group doesn't exist, just return the first group
                    return match.group(1).strip()
        return None

    # function for extracting POI from regex
    def extract_POI(self, text: str) -> Optional[str]:
        patterns = [
            r'(?i)Place of [Ii]ssue\s*[:\/]?\s*([A-Z]+)(?=\n|$)',
            r'[Ii]ssue[^\n]*\n\s*:?\s*([A-Z]+)(?=\n|$)',
            r':\s*([A-Z]+)(?=\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    # function for extracting DOB from regex
    def extract_DOB(self, text: str) -> Optional[str]:
        patterns = [
            r'Date of Birth\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',
            r'(?<=Birth)\s*(\d{2}/\d{2}/\d{4})',
            r'(?:DOB|Birth Date|Birthday)\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',
            r'(?i)(?:birth|dob).*?(\d{2}[\/-]\d{2}[\/-]\d{4})',
            r'\b(\d{2}/\d{2}/\d{4})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                date = match.group(1).strip()
                # Validate date format
                if re.match(r'\d{2}/\d{2}/\d{4}', date):
                    return date
        
        # Additional pattern for finding dates near "Birth" mentions
        birth_section = re.search(r'(?:Birth|DOB).{0,30}', text, re.IGNORECASE)
        if birth_section:
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', birth_section.group(0))
            if date_match:
                return date_match.group(1)
                
        return None
    

    # function for extracting Issue Date from regex
    def extract_IssueDate(self, text: str) -> Optional[str]:
        patterns = [
            r'(\d{2}/\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}',
            r'(?i)Date of Issue\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',
            r'(?:RY\s+art\s+Br\s+Fat|Date of Issue)\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    # function for extracting Issue Date from regex
    def extract_ExpiryDate(self, text: str) -> Optional[str]:
        patterns = [
            r'\d{2}/\d{2}/\d{4}\s+(\d{2}/\d{2}/\d{4})',
            r'(?i)Date of Expiry\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',
            r'(?:SIG\s*&\s*ARI|Date of Expiry)\s*[:\/]?\s*(\d{2}/\d{2}/\d{4})',

        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None

    # function for extracting Sex from regex
    def extract_Sex(self, text: str) -> Optional[str]:
        patterns = [
            r'(?i)Sex\s*[:\/]?\s*([MF])(?=\s|\n|$)',
            r'\d{2}/\d{2}/\d{4}\s+([MF])(?=\s|\n|$)',
            r'(?:fer|Sex)\s*\/?\s*([MF])(?=\s|\n|$)',
            r'\d{2}/\d{2}/\d{4}\s+([MF])\s'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    
class OCRService:
    
    def __init__(self, redis_host="localhost", redis_port=6379, redis_db=0):
        """Initialize OCR service with Redis connection."""
        self.redis_client = redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            db=redis_db
        )
        self.processor = DocumentProcessor(
            self.redis_client,
            tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        )
        
    def process_task(self):
        """Main task processing loop."""
        print("OCR service listening for tasks....")
        
        while True:
            # Block until a task is available
            task = self.redis_client.blpop("ocr_queue", timeout=0)
            
            if task:
                try:
                    # Parse task data
                    task_data = json.loads(task[1])
                    task_id = task_data["taskId"]
                    document_data = task_data["document"]
                    
                    # Process document
                    result = self.processor.process_document(document_data)
                    
                    # Add task metadata
                    result['task_metadata'] = {
                        'task_id': task_id,
                        'processing_time': datetime.now().isoformat()
                    }
                    
                    # Publish result
                    self.redis_client.publish(
                        f"ocr_result_{task_id}",
                        json.dumps(result)
                    )
                    
                    print(f"Processed task {task_id}")
                    
                except Exception as e:
                    error_result = {
                        'error': str(e),
                        'task_id': task_id if 'task_id' in locals() else 'unknown'
                    }
                    self.redis_client.publish(
                        f"ocr_error_{task_id if 'task_id' in locals() else 'unknown'}",
                        json.dumps(error_result)
                    )
                    print(f"Error processing task: {str(e)}")
                    
                    
if __name__ == "__main__":
    service = OCRService()
    service.process_task()