import os
from PIL import Image
import pytesseract
from langfuse.openai import OpenAI
from pathlib import Path
import logging
from common.report_helpers import send_report
from common.ai_helpers import chat_with_gpt

client = OpenAI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_text_from_png(png_file):
    """Extract text from PNG file using OCR."""
    logging.info(f"Extracting text from {png_file}")
    try:
        image = Image.open(png_file)
        text = pytesseract.image_to_string(image)
        logging.info(f"Successfully extracted text from {png_file}")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {png_file}: {str(e)}")
        raise

def save_text_to_file(text, output_file):
    """Save extracted text to a file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)

def get_category(text, filename=None):
    """Use OpenAI to categorize text content."""
    system_prompt = """Categorize the following text into EXACTLY ONE of these categories:
    1. "people" (ONLY if text mentions specific persons who were captured, detected, or identified through surveillance or investigation)
    2. "hardware" (ONLY if text describes actual repair/fixing/maintenance of physical equipment)
    3. "software" (if about software, programming, or digital systems)
    4. "other" (if none of the above)
    
    Rules for categorization:
    - "people" category: ONLY when text describes:
        * Person was detected/captured/identified through surveillance
        * Person's traces or fingerprints were found
        * Person was subject of investigation or detection
        * Just mentioning a person's name without detection/capture context goes to "other"
    - "hardware" category: ONLY when text describes actual repair work or maintenance of equipment
        * Must include repair/fixing/maintenance actions
        * Just mentioning hardware without repair context goes to "other"
    - If in doubt between any category and "other", choose "other"
    
    Think carefully about the content and explain your reasoning. 
    
    IMPORTANT: At the very end, you MUST write ONLY ONE of these EXACT words on a new line (no other words or punctuation allowed):
    people
    hardware
    software
    other
    
    DO NOT use synonyms or alternative words. Use ONLY one of the four words listed above."""

    logging.info(f"Analyzing file: {filename}")
    try:
        response = chat_with_gpt(system_prompt, text)
        
        # Get the last word and remove any punctuation
        category = response.strip().lower().split()[-1].strip('.,!?')
        
        # Validate category
        valid_categories = {'people', 'hardware', 'software', 'other'}
        if category not in valid_categories:
            logging.error(f"Invalid category received for {filename}: {category}")
            raise ValueError(f"Invalid category: {category}")
            
        logging.info(f"File {filename} categorized as: {category}")
        logging.info(f"Full response: {response}")
        return category
    except Exception as e:
        logging.error(f"Error in categorization of {filename}: {str(e)}")
        raise

def prepare_report(categories):
    """Prepare report data with correct file extensions and ordering."""
    files_dir = Path('files')
    report_data = {
        'people': [],
        'hardware': []
    }
    
    # Get all original files (png and mp3)
    png_files = {f.stem: f.name for f in files_dir.glob('*.png')}
    mp3_files = {f.stem: f.name for f in files_dir.glob('*.mp3')}
    
    for category in ['people', 'hardware']:
        if category in categories:
            for txt_file in categories[category]:
                file_stem = Path(txt_file).stem
                
                # Check if this txt was originated from png or mp3
                if file_stem in png_files:
                    report_data[category].append(png_files[file_stem])
                elif file_stem in mp3_files:
                    report_data[category].append(mp3_files[file_stem])
                else:
                    report_data[category].append(txt_file)
            
            # Sort files alphabetically
            report_data[category].sort()
    
    return report_data

def process_files():
    """Main function to process files."""
    logging.info("Starting file processing")
    files_dir = Path('files')
    categories = {
        'people': [],
        'hardware': [],
        'software': [],
        'other': []
    }
    
    # Process PNG files first if corresponding txt doesn't exist
    for file in files_dir.glob('*.png'):
        txt_file = files_dir / f"{file.stem}.txt"
        if not txt_file.exists():
            text = extract_text_from_png(file)
            save_text_to_file(text, txt_file)
    
    # Process all txt files
    for txt_file in files_dir.glob('*.txt'):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Pass filename to get_category
        category = get_category(content, filename=txt_file.name)
        if category != 'software':
            categories[category].append(txt_file.name)
    
    # After processing all files, prepare and send report
    report_data = prepare_report(categories)
    
    try:
        logging.info("Sending report to Centrala")
        response = send_report(report_data, "kategorie")
        logging.info(f"Report sent successfully: {response}")
    except Exception as e:
        logging.error(f"Error sending report: {str(e)}")
        raise

if __name__ == "__main__":
    process_files()
