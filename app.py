import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from resume_screener import extract_text_from_pdf, compute_similarity

app = Flask(__name__)
app.secret_key = 'replace_with_a_random_secret_key'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('base.html')

# 👥 Recruiter Mode (UPDATED)
@app.route('/recruiter', methods=['GET', 'POST'])
def recruiter():
    if request.method == 'POST':
        jd_text = request.form.get('job_description', '').strip()
        if not jd_text:
            flash('Please provide a job description.')
            return redirect(request.url)

        files = request.files.getlist('resumes')
        if not files or all(f.filename == '' for f in files):
            flash('Please upload at least one resume.')
            return redirect(request.url)

        resume_texts = []
        file_names = []

        for f in files:
            if f and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                try:
                    if fname.endswith('.pdf'):
                        text = extract_text_from_pdf(f.stream)
                    else:
                        text = f.read().decode('utf-8', errors='ignore')
                    
                    resume_texts.append(text)
                    file_names.append(fname)
                except Exception as e:
                    flash(f'Error reading file {fname}: {str(e)}')
                    return redirect(request.url)

        if not resume_texts:
            flash('No valid resumes processed.')
            return redirect(request.url)

        try:
            # Pass file_names directly into the function
            results = compute_similarity(jd_text, resume_texts, file_names)
        except Exception as e:
            flash(f'Error computing similarity: {str(e)}')
            return redirect(request.url)

        return render_template('results.html', mode='recruiter', results=results)

    return render_template('recruiter.html')

# 👤 Applicant Mode (UPDATED)
@app.route('/applicant', methods=['GET', 'POST'])
def applicant():
    if request.method == 'POST':
        jd_text = request.form.get('job_description', '').strip()
        if not jd_text:
            flash('Please provide a job description.')
            return redirect(request.url)

        file = request.files.get('resume')
        if not file or file.filename == '':
            flash('Please upload a resume (PDF or TXT).')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Unsupported file type. Use PDF or TXT.')
            return redirect(request.url)

        fname = secure_filename(file.filename)

        try:
            if fname.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file.stream)
            else:
                resume_text = file.read().decode('utf-8', errors='ignore')
        except Exception as e:
            flash(f'Error reading file: {str(e)}')
            return redirect(request.url)

        try:
            # Pass fname as a single item list
            results = compute_similarity(jd_text, [resume_text], [fname])
        except Exception as e:
            flash(f'Error computing similarity: {str(e)}')
            return redirect(request.url)

        return render_template('results.html', mode='applicant', results=results)

    return render_template('applicant.html')

if __name__ == '__main__':
    app.run(debug=True)