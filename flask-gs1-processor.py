import os
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
import your_gs1_processing_script  # Import your existing processing script

app = Flask(__name__)

# Configure upload and processing directories
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'tiff', 'tif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            return 'No file part', 400
        
        file = request.files['file']
        
        # If no selected file
        if file.filename == '':
            return 'No selected file', 400
        
        # If file is valid
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], f'processed_{filename}')
            
            # Save uploaded file
            file.save(input_path)
            
            # Process the image using your existing script
            try:
                your_gs1_processing_script.process_image(input_path, output_path)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f'Processing error: {str(e)}', 500
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
