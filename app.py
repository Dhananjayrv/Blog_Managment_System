from flask import Flask, render_template, request, redirect, url_for, flash, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.utils import secure_filename
from PIL import Image
import os
import shutil
import time
import subprocess  # Import subprocess module for PDF generation
import zipfile

app = Flask(__name__)
app.secret_key = 'kdhananjay444'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'upload_folder'  # Update this line
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=False)

owner_credentials = {'rv': 'rv@82102'}

@app.route('/')
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/course') 
def course():
    return render_template('course.html')

@app.route('/blog')
def blog():
    posts = Post.query.all()
    return render_template('blog.html', posts=posts)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'rv' and password == owner_credentials['rv']:
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('signin.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        if 'title_to_edit' in request.form:
            title_to_edit = request.form['title_to_edit']
            post_to_edit = Post.query.filter_by(title=title_to_edit).first()

            if post_to_edit:
                return render_template('edit_blog.html', post=post_to_edit)
            else:
                flash('Blog post not found. Please enter a valid title.')
                return redirect(url_for('dashboard'))

        elif 'title_to_delete' in request.form:
            title_to_delete = request.form['title_to_delete']
            post_to_delete = Post.query.filter_by(title=title_to_delete).first()

            if post_to_delete:
                db.session.delete(post_to_delete)
                db.session.commit()
                flash('Blog post deleted successfully!')
            else:
                flash('Blog post not found. Please enter a valid title.')

    posts = Post.query.all()
    return render_template('dashboard.html', posts=posts)

@app.route('/delete_blog', methods=['POST'])
def delete_blog():
    title_to_delete = request.form['title_to_delete']
    post_to_delete = Post.query.filter_by(title=title_to_delete).first()

    if post_to_delete:
        try:
            image_path = os.path.join('static/images', post_to_delete.image)
            os.remove(image_path)
        except FileNotFoundError:
            pass

        db.session.delete(post_to_delete)
        db.session.commit()
        flash('Blog post deleted successfully!')
        return redirect(url_for('home'))
    else:
        flash('Blog post not found. Please enter a valid title.')

    return redirect(url_for('home'))

@app.route('/edit_blog', methods=['GET', 'POST'])
def edit_blog():
    if request.method == 'POST':
        title_to_edit = request.form['title_to_edit']
        post_to_edit = Post.query.filter_by(title=title_to_edit).first()

        if post_to_edit:
            try:
                post_to_edit.title = request.form['title']
                post_to_edit.content = request.form['content']
                
                image = request.files['image']

                if image:
                    image.save(os.path.join('static/images', image.filename))
                    post_to_edit.image = image.filename

                db.session.commit()
                flash('Blog post updated successfully!')
                return redirect(url_for('home'))
            except Exception as e:
                flash(f'Error updating blog post: {str(e)}')
        else:
            flash('Blog post not found. Please enter a valid title.')

    posts = Post.query.all()
    return render_template('dashboard.html', posts=posts)

@app.route('/add_blog', methods=['POST'])
def add_post():
    title = request.form['title']
    content = request.form['content']
    image = request.files['image']

    image.save(f'static/images/{image.filename}')

    new_post = Post(title=title, content=content, image=image.filename)
    db.session.add(new_post)
    db.session.commit()

    flash('Thank you for adding a new blog!')
    time.sleep(2)

    return redirect(url_for('blog'))

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get(post_id)
    return render_template('post_detail.html', post=post)

@app.route('/detail')
def detail():
    return render_template('detail.html')

@app.route('/feature')
def feature():
    return render_template('feature.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/testimonial')
def testimonial():
    return render_template('testimonial.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/join_us')
def join_us():
    return render_template('join_us.html')

@app.route('/download_blog', methods=['POST'])
def download_blog():
    title_to_download = request.form['title_to_download']
    post_to_download = Post.query.filter_by(title=title_to_download).first()

    if post_to_download:
        folder_name = f'{title_to_download}_blog'
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)

        # Save the text information to a TXT file
        txt_file_path = os.path.join(folder_path, f'{title_to_download}_info.txt')
        with open(txt_file_path, 'w') as txt_file:
            txt_file.write(f'Title: {post_to_download.title}\n\n')
            txt_file.write(f'Content:\n{post_to_download.content}')

        # Save the image in JPEG format
        image_path = os.path.join('static/images', post_to_download.image)
        image_file_path = os.path.join(folder_path, f'{title_to_download}_image.jpg')
        with Image.open(image_path) as img:
            img.convert('RGB').save(image_file_path, 'JPEG')

        # Create a zip file
        zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{title_to_download}_blog.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            zip_file.write(txt_file_path, f'{title_to_download}_info.txt')
            zip_file.write(image_file_path, f'{title_to_download}_image.jpg')

        # Return the zip file as a download
        return send_file(zip_file_path, as_attachment=True)

    else:
        flash('Blog post not found. Please enter a valid title.')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
