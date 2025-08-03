from flask import Flask, render_template, request, send_file
from database.resume_db import create_database, save_resume, get_resume
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/generated'

# Ensure required folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Initialize database
create_database()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle photo upload
        photo = request.files.get('photo')
        photo_filename = ''
        if photo and photo.filename:
            photo_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
            photo.save(os.path.join('static/uploads', photo_filename))

        # Gather form data
        resume_data = {
            'name': request.form.get('name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'dob': request.form.get('dob', ''),
            'address': request.form.get('address', ''),
            'nationality': request.form.get('nationality', ''),
            'linkedin': request.form.get('linkedin', ''),
            'skills': request.form.getlist('skills'),
            'languages': request.form.getlist('languages'),
            'hobbies': request.form.getlist('hobbies'),
            'objective': request.form.get('objective', ''),
            'experience': request.form.get('experience', ''),
            'education': request.form.get('education', ''),
            'declaration': request.form.get('declaration', 'I hereby declare that the information provided is true to the best of my knowledge.'),
            'date': datetime.now().strftime("%d/%m/%Y"),
            'photo': photo_filename
        }

        # Save to DB
        resume_id = save_resume(resume_data)

        # Generate PDF
        pdf_path = generate_pdf(resume_data, resume_id)

        return send_file(pdf_path, as_attachment=True)

    return render_template('resume_form.html')


def generate_pdf(resume_data, resume_id):
    # Construct full image path
    if resume_data['photo']:
        photo_abs_path = os.path.abspath(os.path.join('static/uploads', resume_data['photo']))
        import base64

        with open(photo_abs_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            resume_data['photo_path'] = f"data:image/jpeg;base64,{encoded_string}"
    else:
        resume_data['photo_path'] = ''

    # Load and render HTML template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('resume_template.html')
    html_out = template.render(resume_data)

    # Generate and save PDF
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{resume_id}.pdf")
    HTML(string=html_out, base_url='.').write_pdf(pdf_path)

    return pdf_path


@app.route('/view/<int:resume_id>')
def view_resume(resume_id):
    resume = get_resume(resume_id)
    if resume:
        resume['photo_path'] = f"/static/uploads/{resume['photo']}"  # For browser view
        return render_template('resume_template.html', **resume)
    return "Resume not found", 404


@app.route('/download/<int:resume_id>')
def download_resume(resume_id):
    resume = get_resume(resume_id)
    if resume:
        pdf_path = generate_pdf(resume, resume_id)
        return send_file(pdf_path, as_attachment=True)
    return "Resume not found", 404


@app.route('/debug/<int:resume_id>')
def debug_view(resume_id):
    resume = get_resume(resume_id)
    resume['photo_path'] = f"/static/uploads/{resume['photo']}"  # for debugging in browser
    return render_template('resume_template.html', **resume)


if __name__ == '__main__':
    app.run(debug=True)