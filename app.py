import io
import os
import dotenv
from flask import Flask, redirect, render_template, request, send_file, url_for
import pandas as pd
from chat2plot import chat2plot
from langchain_community.chat_models import ChatOpenAI
import plotly.io as pio
from plotly.io import to_image
from werkzeug.utils import secure_filename


dotenv.load_dotenv()    
api = os.getenv('api_key')

os.environ["OPENAI_API_KEY"] = api

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'csv', 'xls', 'xlsx'}

@app.route("/")
def home():
    return redirect(url_for('upload'))
    

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':

        if 'file' not in request.files:
            error_message = "No file part"
            return render_template('upload.html', error_message=error_message)
        
        uploaded_file = request.files['file']
        
        if uploaded_file.filename == '':
            error_message = "No selected file"
            return render_template('upload.html', error_message=error_message)
        
        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename) 
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                uploaded_file.save(file_path)
                
                if filename.endswith('.xls') or filename.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                elif filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    error_message = "Unsupported file type"
                    return render_template('upload.html', error_message=error_message)
                
                csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted_data.csv')
                df.to_csv(csv_file_path, index=False)

                os.remove(file_path)
                
                return redirect(url_for('index'))
            
            except Exception as e:
                error_message = f"An error occurred while saving or converting the file: {str(e)}"
                return render_template('upload.html', error_message=error_message)
        
        else:
            error_message = "Allowed file types are txt, csv, xls, xlsx"
            return render_template('upload.html', error_message=error_message)
    
    return render_template('upload.html')


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        
        df = pd.read_csv(f"uploads/converted_data.csv")

        try:
            c2p = chat2plot(df.copy(), chat=ChatOpenAI(model='gpt-3.5-turbo'))
            result = c2p(query)
            graph_html = pio.to_html(result.figure, full_html=False)
            graph = result.figure
            explanation = result.explanation
            return render_template('index.html', graph_html=graph_html, explanation=explanation, query=query)
        except Exception as e:
            error_message = str(e)
            return render_template('index.html', error_message=error_message)
    else:
        return render_template('index.html')
    
# @app.route('/generate_plot', methods=['POST'])
# def saveGraph():
#     global graph

#     image_bytes = to_image(graph, format="png")

#     with open("plot.png", "wb") as f:
#         f.write(image_bytes)
        
# @app.route("/promptSuggestion")
# def promptSuggestion():
#     return render_template('promptSuggestion.html')

if __name__ == '__main__':
    app.run(debug=True)
