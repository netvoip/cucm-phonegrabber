#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import get_phones_sn
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import fields, StringField, TextAreaField, SubmitField, SelectField, validators
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config.update(dict(SECRET_KEY="powerful secretkey",
    WTF_CSRF_SECRET_KEY="a csrf secret key"))

class MainForm(FlaskForm):
  num = StringField("Number mask", [validators.Required("Please enter mask")], default="*",
      render_kw={'maxlength': 5})
  model = SelectField('Model',
        choices=[('255', 'Any'), ('592', 'Cisco 3905'), ('36213', 'Cisco 7811'), ('621', 'Cisco 7821')], default="255")
  message = TextAreaField("Message")
  submit = SubmitField("Send")

@app.route("/", methods=['GET', 'POST'])
def a():
    form = MainForm()
    out = ''
    maintext = ''
    num = form.num.data
    model = form.model.data
    if form.validate_on_submit():
        out = get_phones_sn.getphonessn(model = model, num = num, ip = '', name = '', max = 1500)
    return render_template('index.html', maintext=str(out), form = form)


if __name__ == '__main__':
     app.run()