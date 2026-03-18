import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
# app.py - CORRECT
app = Flask(__name__)
# ... all route definitions

# Import at the END
from resume_screener import extract_text_from_pdf, compute_similarity
app.secret_key = 'replace_with_a_random_secret_key'

# Folder to store uploaded PDFs temporarily
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/recruiter', methods=['GET', 'POST'])


@app.route('/recruiter', methods=['GET', 'POST'])
def recruiter():
    if request.method == 'POST':
        # 1️⃣ Job description
        jd_text = request.form.get('job_description', '').strip()
        if not jd_text:
            flash('Please provide a job description.')
            return redirect(request.url)

        # 2️⃣ Resumes
        files = request.files.getlist('resumes')
        if not files or all(f.filename == '' for f in files):
            flash('Please upload at least one resume.')
            return redirect(request.url)

        # Extract text
        resume_texts = []
        file_names = []
        for f in files:
            if f and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                if fname.endswith('.pdf'):
                    txt = extract_text_from_pdf(f.stream)
                else:
                    txt = f.read().decode('utf-8', errors='ignore')
                resume_texts.append(txt)
                file_names.append(fname)

        # DEBUG: Print what we received
        print(f"JD length: {len(jd_text)}")
        print(f"Number of resumes: {len(resume_texts)}")
        print(f"File names: {file_names}")

        # 3️⃣ Compute scores
        try:
            results = compute_similarity(jd_text, resume_texts)
            print(f"Results count: {len(results)}")
            print(f"Results: {results}")  # DEBUG
        except Exception as e:
            print(f"Error: {e}")  # DEBUG
            flash(str(e))
            return redirect(request.url)

        # Attach original filenames
        for r, name in zip(results, file_names):
            r['resume_name'] = name

        print(f"Final results: {results}")  # DEBUG
        
        return render_template('results.html', mode='recruiter', results=results)

    return render_template('recruiter.html')
@app.route('/applicant', methods=['GET', 'POST'])
def applicant():
    if request.method == 'POST':
        jd_text = request.form.get('job_description', '').strip()
        if not jd_text:
            flash('Please provide a job description.')
            return redirect(request.url)

        file = request.files.get('resume')
        if not file or file.filename == '':
            flash('Please upload a resume.')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            if fname.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file.stream)
            else:
                resume_text = file.read().decode('utf-8', errors='ignore')
        else:
            flash('Unsupported file type.')
            return redirect(request.url)

        # DEBUG
        print(f"JD: {jd_text[:50]}...")
        print(f"Resume: {fname}")
        
        try:
            results = compute_similarity(jd_text, [resume_text])
            print(f"Results: {results}")
        except Exception as e:
            print(f"Error: {e}")
            flash(str(e))
            return redirect(request.url)

        results[0]['resume_name'] = fname
        return render_template('results.html', mode='applicant', results=results)

    return render_template('applicant.html')

@app.route('/applicant', methods=['GET', 'POST'])
def applicant():
    if request.method == 'POST':
        # 1️⃣ Job description
        jd_text = request.form.get('job_description', '').strip()
        if not jd_text:
            flash('Please provide a job description.')
            return redirect(request.url)

        # 2️⃣ Resume
        file = request.files.get('resume')
        if not file or file.filename == '':
            flash('Please upload a resume (PDF or TXT).')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            if fname.endswith('.pdf'):
                resume_text = extract_text_from_pdf(file.stream)
            else:
                resume_text = file.read().decode('utf-8', errors='ignore')
        else:
            flash('Unsupported file type.')
            return redirect(request.url)

        # 3️⃣ Compute score (single resume)
        try:
            results = compute_similarity(jd_text, [resume_text])
        except Exception as e:
            flash(str(e))
            return redirect(request.url)

        # Attach filename
        results[0]['resume_name'] = fname
        return render_template('results.html', mode='applicant', results=results)

    return render_template('applicant.html')

# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Development server
    app.run(debug=True)