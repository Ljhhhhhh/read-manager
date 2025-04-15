import os
from werkzeug.utils import secure_filename
from flask import Flask, send_file, render_template, request, redirect, url_for, flash, session, send_from_directory, abort

app = Flask(__name__, template_folder='src')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'src', 'uploaded_pages')
ALLOWED_EXTENSIONS = {'html', 'htm'}

# Fixed credentials
USERNAME = 'lujiehui'
PASSWORD = 'Guanmo!01'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Function to Get Pages ---
def get_uploaded_pages():
    """Returns a sorted list of dictionaries for pages in the upload folder."""
    pages = []
    upload_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        for filename in sorted(os.listdir(upload_folder)):
            if allowed_file(filename):
                 path_name = os.path.splitext(filename)[0]
                 pages.append({'filename': filename, 'path': path_name})
    return pages

# --- Public Routes ---
@app.route("/")
def index():
    """Serves the main index page which lists resources."""
    available_pages = get_uploaded_pages()
    # Render index.html directly, passing the list of pages
    return render_template('index.html', pages=available_pages)

# REMOVED the /resources route as it's now handled by index

@app.route('/page/<page_name>')
def serve_uploaded_page(page_name):
    """Serves an uploaded HTML page."""
    filename = f"{page_name}.html"
    secure_file = secure_filename(filename)

    file_path_abs = os.path.join(app.config['UPLOAD_FOLDER'], secure_file)
    if os.path.commonpath([app.config['UPLOAD_FOLDER']]) != os.path.commonpath([app.config['UPLOAD_FOLDER'], file_path_abs]):
         abort(404)

    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], secure_file)
    except FileNotFoundError:
        try:
            filename_htm = f"{page_name}.htm"
            secure_file_htm = secure_filename(filename_htm)
            file_path_abs_htm = os.path.join(app.config['UPLOAD_FOLDER'], secure_file_htm)
            if os.path.commonpath([app.config['UPLOAD_FOLDER']]) != os.path.commonpath([app.config['UPLOAD_FOLDER'], file_path_abs_htm]):
                abort(404)
            return send_from_directory(app.config['UPLOAD_FOLDER'], secure_file_htm)
        except FileNotFoundError:
            abort(404)

# --- Login/Logout/Admin Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash('Successfully logged in', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid Credentials. Please try again.', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        flash('Please log in to access the admin area.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':
            if 'html_file' not in request.files:
                flash('No file part in request.', 'error')
                return redirect(request.url)
            file = request.files['html_file']
            if file.filename == '':
                flash('No file selected for upload.', 'error')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                provided_path = request.form.get('path_name', '').strip()
                safe_path_name = ""

                if provided_path:
                    safe_path_name = "".join(c for c in provided_path if c.isalnum() or c == '-')
                    if not safe_path_name:
                         flash('Invalid characters in Access Path Name. Using filename instead.', 'warning')
                         safe_path_name = os.path.splitext(original_filename)[0]
                else:
                     safe_path_name = os.path.splitext(original_filename)[0]

                save_filename = f"{safe_path_name}.html"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)

                if os.path.exists(save_path):
                     flash(f'Error: A page with the path "/page/{safe_path_name}" (file: {save_filename}) already exists.', 'error')
                else:
                    try:
                        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                        file.save(save_path)
                        flash(f'Page "{safe_path_name}" uploaded successfully! Access at /page/{safe_path_name}', 'success')
                    except Exception as e:
                         flash(f'An error occurred during upload: {e}', 'error')
            else:
                flash('Invalid file type. Only .html and .htm files allowed.', 'error')

        elif action == 'delete':
            filename_to_delete = request.form.get('filename_to_delete')
            if not filename_to_delete:
                 flash('No filename provided for deletion.', 'error')
            else:
                safe_filename = secure_filename(filename_to_delete)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

                if os.path.commonpath([app.config['UPLOAD_FOLDER']]) != os.path.commonpath([app.config['UPLOAD_FOLDER'], file_path]):
                     flash('Deletion path error.', 'error')
                elif os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        flash(f'File "{safe_filename}" deleted successfully.', 'success')
                    except Exception as e:
                        flash(f'Error deleting file "{safe_filename}": {e}', 'error')
                else:
                    flash(f'File "{safe_filename}" not found for deletion.', 'error')

        return redirect(url_for('admin'))

    uploaded_pages = get_uploaded_pages()
    return render_template('admin.html', uploaded_pages=uploaded_pages)

# --- Main Execution ---
def main():
    app.template_folder = os.path.join(os.path.dirname(__file__), 'src')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    main()
