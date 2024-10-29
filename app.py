from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from fpdf import FPDF
from sqlalchemy import create_engine, Column, Integer, String, DateTime, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Database connection
DATABASE_URL = 'mysql+pymysql://reporter:Werwach01042001!@localhost/rt5'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

#Webapp credentials
users = {
    'operator1': 'J6p4g1rXekzzjuNquO9K',
    'operator2': 'J6p4g1rXekzzjuNquO9K'
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class Ticket(Base):
    __tablename__ = 'Tickets'
    id = Column(Integer, primary_key=True)
    Subject = Column(String(255))
    Priority = Column(Integer)
    Queue = Column(Integer)
    Created = Column(DateTime)

@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    start_datetime_str = request.form['start_datetime']
    end_datetime_str = request.form['end_datetime']

    try:
        start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        flash('Nieprawidłowy format daty i czasu. Proszę podać daty w formacie YYYY-MM-DDTHH:MM.', 'error')
        return redirect(url_for('index'))

    session = Session()

    tickets = session.query(Ticket).filter(
        and_(Ticket.Created.between(start_datetime, end_datetime),
             Ticket.Queue.in_([4, 5]))
    ).all()

    if not tickets:
        flash('Brak danych w podanym przedziale czasowym.', 'warning')
        return redirect(url_for('index'))

    df = pd.DataFrame([(ticket.id, ticket.Queue, ticket.Priority) for ticket in tickets], 
                      columns=['id', 'Queue', 'Priority'])

    zgłoszenia = df[df['Queue'] == 4]
    incydenty = df[df['Queue'] == 5]

    zgłoszenia_summary = zgłoszenia['Priority'].value_counts().reindex([100, 50, 0], fill_value=0).astype(int) if not zgłoszenia.empty else None
    incydenty_summary = incydenty['Priority'].value_counts().reindex([100, 50, 0], fill_value=0).astype(int) if not incydenty.empty else None

    def generate_pie_chart(data, title):
        plt.figure(figsize=(5, 5))
        labels = ['High', 'Medium', 'Low']
        sizes = [data[100], data[50], data[0]]
        colors = ['#ff6666', '#ffcc99', '#66b3ff']
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title(title)
        plt.axis('equal')

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()
        return img_buffer

    zgłoszenia_chart = (generate_pie_chart(zgłoszenia_summary, "") if zgłoszenia_summary is not None 
                        and zgłoszenia_summary.nunique() > 0 and zgłoszenia_summary.sum() > 0 else None)
    incydenty_chart = (generate_pie_chart(incydenty_summary, "") if incydenty_summary is not None 
                       and incydenty_summary.nunique() > 0 and incydenty_summary.sum() > 0 else None)


    pdf = FPDF()
    pdf.add_page()

    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 100, "", ln=True, align='C')
    pdf.image("soc.png", x=60, w=90)
    pdf.cell(0, 100, "SOC Incidents Report", ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Created: '+datetime.now().strftime("%d-%m-%Y"), ln=True, align='C')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.cell(0, 10, "Incidents Summary", ln=True)
    pdf.cell(200, 10, "", ln=True)

    total_rep = len(zgłoszenia)
    total_incydenty = len(incydenty)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"The report below is a daily report describing the number of incidents handled by the Security Operations Center team.", ln=True)
    pdf.cell(0, 10, f"The report has been created "+datetime.now().strftime("%d-%m-%Y")+".", ln=True)
    pdf.cell(0, 10, f"This report covers the time period between "+start_datetime+" and "+end_datetime, ln=True) 
    pdf.cell(0, 10, f"In the time period covered by the report, we registered "+str(total_rep)+" incident reports, based on which we undertook", ln=True)
    pdf.cell(0, 10, f"an investigation and created "+str(total_incydenty)+ " incidents.", ln=True)
    pdf.cell(0, 10, f"Below we present the exact number of reports and incidents divided by priority", ln=True) 
    pdf.cell(0, 10, f"", ln=True)
    pdf.cell(0, 10, f"", ln=True)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(200, 10, "Requests:", ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(200, 10, f"High: {zgłoszenia_summary[100]}", ln=True)
    pdf.cell(200, 10, f"Medium: {zgłoszenia_summary[50]}", ln=True)
    pdf.cell(200, 10, f"Low: {zgłoszenia_summary[0]}", ln=True)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, f"", ln=True)
    if incydenty_summary is not None:
        pdf.set_font('Arial', 'B', 13)
        pdf.cell(0, 10, "Incidents", ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f"High: {incydenty_summary[100]}", ln=True)
        pdf.cell(0, 10, f"Medium: {incydenty_summary[50]}", ln=True)
        pdf.cell(0, 10, f"Low: {incydenty_summary[0]}", ln=True)


    pdf.add_page()
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, "Incidents handled between "+start_datetime+" and "+end_datetime, ln=True)
    pdf.cell(0, 10, f"", ln=True)

    #Report table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, "Date", border=1, align='C')
    pdf.cell(80, 10, "Subject", border=1, align='C')
    pdf.cell(50, 10, "Type", border=1, ln=True, align='C')

    pdf.set_font('Arial', '', 10)

    for ticket in tickets:
        data = ticket.Created
        temat = ticket.Subject
        typ_zgloszenia = "Incident Report" if ticket.Queue == 4 else "Incident"

        pdf.cell(50, 10, data, border=1, align='C')
        pdf.cell(80, 10, temat, border=1, align='C')
        pdf.cell(50, 10, typ_zgloszenia, border=1, ln=True, align='C')



    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "Graphs showing the number of incidents handled:", ln=True)
    pdf.cell(0, 10, "", ln=True)
    if zgłoszenia_chart:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Requests", ln=True, align='C')
        pdf.image(zgłoszenia_chart, x=60, w=90)

    if incydenty_chart:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Incidents", ln=True, align='C')
        pdf.image(incydenty_chart, x=60, w=90)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return send_file(pdf_output, as_attachment=True, download_name='SOC_Report_'+datetime.now().strftime("%d-%m-%Y")+'.pdf')

if __name__ == '__main__':
    app.run(debug=True)

