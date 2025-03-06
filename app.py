from flask import Flask, request, render_template, send_file
from PyPDF2 import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import os

app = Flask(__name__)

def add_header_to_pdf(pdf_file, png_path, scale_factor=0.5, header_height=100):
    pdf_reader = PdfReader(pdf_file)
    pdf_writer = PdfWriter()
    
    img = ImageReader(png_path)
    img_width, img_height = img.getSize()
    
    img_width = img_width * scale_factor
    img_height = img_height * scale_factor
    
    header_height = max(header_height, img_height)

    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)
        
        new_height = original_height + header_height
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(original_width, new_height))
        
        can.setFillColorRGB(1, 1, 1)
        can.rect(0, original_height, original_width, header_height, fill=1, stroke=0)
        
        x_pos = (original_width - img_width) / 2
        y_pos = original_height
        
        can.drawImage(png_path, x_pos, y_pos, width=img_width, height=img_height,
                     preserveAspectRatio=True, mask='auto')
        
        can.save()
        packet.seek(0)
        
        header_pdf = PdfReader(packet)
        header_page = header_pdf.pages[0]
        
        page.add_transformation(Transformation().translate(0, 0))
        header_page.merge_page(page)
        
        pdf_writer.add_page(header_page)
    
    output = io.BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded", 400
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.pdf'):
            return "Please upload a valid PDF file", 400
        
        png_path = os.path.join(app.root_path, 'static', 'header.png')
        if not os.path.exists(png_path):
            return "Header image not found on server", 500
        
        output_pdf = add_header_to_pdf(file, png_path, scale_factor=0.5)
        
        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='output_with_header.pdf'
        )
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Use PORT env var or 8080
    app.run(host='0.0.0.0', port=port, debug=False)