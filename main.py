import os
import json
from werkzeug.utils import secure_filename
from flask import Flask, send_file, render_template, request, redirect, url_for, flash, session, send_from_directory, abort

app = Flask(__name__, template_folder='src')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'src', 'uploaded_pages')
app.config['COVER_FOLDER'] = os.path.join(os.path.dirname(__file__), 'src', 'covers')
app.config['METADATA_FILE'] = os.path.join(os.path.dirname(__file__), 'src', 'metadata.json')
ALLOWED_EXTENSIONS = {'html', 'htm'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Fixed credentials
USERNAME = 'lujiehui'
PASSWORD = 'Guanmo!01'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# --- Helper Functions for Metadata ---
def load_metadata():
    """Load metadata from JSON file"""
    if os.path.exists(app.config['METADATA_FILE']):
        try:
            with open(app.config['METADATA_FILE'], 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_metadata(metadata):
    """Save metadata to JSON file"""
    os.makedirs(os.path.dirname(app.config['METADATA_FILE']), exist_ok=True)
    with open(app.config['METADATA_FILE'], 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

# --- Helper Function to Get Pages ---
def get_uploaded_pages():
    """Returns a sorted list of dictionaries for pages in the upload folder."""
    pages = []
    upload_folder = app.config['UPLOAD_FOLDER']
    metadata = load_metadata()
    
    if os.path.exists(upload_folder):
        for filename in sorted(os.listdir(upload_folder)):
            if allowed_file(filename):
                path_name = os.path.splitext(filename)[0]
                page_data = {'filename': filename, 'path': path_name}
                
                # Add metadata if available
                if path_name in metadata:
                    page_data.update(metadata[path_name])
                    
                pages.append(page_data)
    return pages

# --- Public Routes ---
@app.route("/")
def index():
    """Serves the main index page which lists resources."""
    available_pages = get_uploaded_pages()
    # Render index.html directly, passing the list of pages
    return render_template('index.html', pages=available_pages)

@app.route('/covers/<filename>')
def serve_cover(filename):
    """Serves a cover image"""
    return send_from_directory(app.config['COVER_FOLDER'], filename)

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
                article_title = request.form.get('article_title', '').strip()
                safe_path_name = ""

                if provided_path:
                    safe_path_name = "".join(c for c in provided_path if c.isalnum() or c == '-')
                    if not safe_path_name:
                         flash('访问路径名称包含无效字符，将使用文件名代替', 'warning')
                         safe_path_name = os.path.splitext(original_filename)[0]
                else:
                     safe_path_name = os.path.splitext(original_filename)[0]

                save_filename = f"{safe_path_name}.html"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_filename)

                if os.path.exists(save_path):
                     flash(f'错误：路径为 "/page/{safe_path_name}" 的页面 (文件: {save_filename}) 已存在', 'error')
                else:
                    try:
                        # 保存HTML文件
                        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                        file.save(save_path)
                        
                        # 处理封面图片
                        cover_filename = None
                        if 'article_cover' in request.files:
                            cover_file = request.files['article_cover']
                            if cover_file and cover_file.filename != '' and allowed_image_file(cover_file.filename):
                                cover_ext = cover_file.filename.rsplit('.', 1)[1].lower()
                                cover_filename = f"{safe_path_name}.{cover_ext}"
                                os.makedirs(app.config['COVER_FOLDER'], exist_ok=True)
                                cover_file.save(os.path.join(app.config['COVER_FOLDER'], cover_filename))
                        
                        # 保存元数据
                        metadata = load_metadata()
                        metadata[safe_path_name] = {
                            'title': article_title,
                            'cover': cover_filename
                        }
                        save_metadata(metadata)
                        
                        flash(f'页面 "{article_title}" 上传成功！访问路径：/page/{safe_path_name}', 'success')
                    except Exception as e:
                         flash(f'上传过程中发生错误: {e}', 'error')
            else:
                flash('无效的文件类型。仅允许 .html 和 .htm 文件', 'error')

        elif action == 'delete':
            filename_to_delete = request.form.get('filename_to_delete')
            if not filename_to_delete:
                 flash('未提供要删除的文件名', 'error')
            else:
                safe_filename = secure_filename(filename_to_delete)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
                path_name = os.path.splitext(safe_filename)[0]

                if os.path.commonpath([app.config['UPLOAD_FOLDER']]) != os.path.commonpath([app.config['UPLOAD_FOLDER'], file_path]):
                     flash('删除路径错误', 'error')
                elif os.path.exists(file_path):
                    try:
                        # 删除HTML文件
                        os.remove(file_path)
                        
                        # 删除相关的封面图片
                        metadata = load_metadata()
                        if path_name in metadata and 'cover' in metadata[path_name] and metadata[path_name]['cover']:
                            cover_path = os.path.join(app.config['COVER_FOLDER'], metadata[path_name]['cover'])
                            if os.path.exists(cover_path):
                                os.remove(cover_path)
                        
                        # 从元数据中删除
                        if path_name in metadata:
                            del metadata[path_name]
                            save_metadata(metadata)
                            
                        flash(f'文件 "{safe_filename}" 删除成功', 'success')
                    except Exception as e:
                        flash(f'删除文件 "{safe_filename}" 时出错: {e}', 'error')
                else:
                    flash(f'未找到要删除的文件 "{safe_filename}"', 'error')

        return redirect(url_for('admin'))

    uploaded_pages = get_uploaded_pages()
    return render_template('admin.html', uploaded_pages=uploaded_pages)

# --- Main Execution ---
def main():
    app.template_folder = os.path.join(os.path.dirname(__file__), 'src')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['COVER_FOLDER'], exist_ok=True)
    main()
