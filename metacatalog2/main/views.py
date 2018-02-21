from flask import render_template

from metacatalog2.main import main


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/add')
def add():
    return render_template('add_form.html')
