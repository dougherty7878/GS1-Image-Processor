from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageChops
import os
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff', 'tif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def apply_gs1_clipping(input_path, output_path, target_width=3000, target_height=3000, dpi=300):
    try:
        # Process image similar to previous desktop application
        img = Image.open(input_path).convert("RGBA")
        bbox = ImageChops.difference(img, Image.new("RGBA", img.size, (255,255,255,255))).getbbox()
        
        if not bbox:
            raise ValueError("No content found in image")
        
        img_cropped = img.crop(bbox)
        canvas = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 255))
        
        img_ratio = img_cropped.width / img_cropped.height
        canvas_ratio = canvas.width / canvas.height
        
        if img_ratio > canvas_ratio:
            new_width = canvas.width
            new_height = int(new_width / img_ratio)
        else:
            new_height = canvas.height
            new_width = int(new_height * img_ratio)
        
        img_resized = img_cropped.resize((new_width, new_height), Image.LANCZOS)
        paste_x = (canvas.width - new_width) // 2
        paste_y = (canvas.height - new_height) // 2
        
        canvas.paste(img_resized, (paste_x, paste_y), img_resized)
        canvas.info['dpi'] = (dpi, dpi)
        canvas.save(output_path, quality=95, dpi=(dpi, dpi))
        return True
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files')
    processed_files = []

    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
            output_filename = f"gs1_{unique_id}_{filename.split('.')[0]}.tiff"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Save and process file
            file.save(input_path)
            if apply_gs1_clipping(input_path, output_path):
                processed_files.append(output_filename)
            
            # Remove input file
            os.remove(input_path)
    
    return jsonify({
        'processed_files': processed_files,
        'total_processed': len(processed_files)
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
