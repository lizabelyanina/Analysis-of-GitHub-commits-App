from flask import Flask, render_template, request, send_file, url_for
import os
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from functional import lifecycle_duration_plot, is_public_github_repo, basic_stats, generate_plots, get_plot_url, generate_ocdfg, convert_to_ocel_and_get_summary, generate_text_summary, generate_ocpn, contributor_analysis
from repo_parser import process_github_repo
from label_classific import predict
import tempfile

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['TEMP_FOLDER'] = tempfile.mkdtemp()

@app.route('/', methods=['GET', 'POST'])
def index():
    user_input = ''
    result = ''
    download_links = []
    preview = None
    plots = None
    contributor_data = None
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        
        if is_public_github_repo(user_input):
            is_conventional_standard = False
            if request.form.get('checkbox'):
                is_conventional_standard = True
                df, branches_map = process_github_repo(user_input, conventional_commits=is_conventional_standard)
            else:
                df, branches_map = process_github_repo(user_input, conventional_commits=is_conventional_standard)
                df['ocel:activity'] = [predict(message) for message in df['commit_message']]
            
            # Save data.csv
            csv_filename = 'data.csv'
            csv_path = os.path.join(app.config['TEMP_FOLDER'], csv_filename)
            df.to_csv(csv_path, index=False)
            download_links.append(('data.csv', url_for('download_file', filename=csv_filename)))
            
            # Generate ocdfg.png
            ocel_data, temporal_summary, objects_summary = convert_to_ocel_and_get_summary(df)
            ocdfg_filename = 'ocdfg.png'
            ocdfg_path = os.path.join(app.config['TEMP_FOLDER'], ocdfg_filename)
            generate_ocdfg(ocel_data, ocdfg_path)
            download_links.append(('ocdfg.png', url_for('download_file', filename=ocdfg_filename)))
            
            # Generate ocpn.png
            ocpn_filename = 'ocpn.png'
            ocpn_path = os.path.join(app.config['TEMP_FOLDER'], ocpn_filename)
            generate_ocpn(ocel_data, ocpn_path)
            download_links.append(('ocpn.png', url_for('download_file', filename=ocpn_filename)))
            
            unique_contributors, average_commits_per_contributor = basic_stats(df)
            
            result = generate_text_summary(df, ocel_data, objects_summary)

            # Generate preview
            preview = df.head().to_html(classes='table table-striped table-hover', index=False)

            # Generate plots
            plots = generate_plots(df)

            # Generate contributor analysis
            contributor_data = contributor_analysis(df)
        
        else:
            result = "The input is not a valid GitHub link to a public repository."
    return render_template('index.html', user_input=user_input, result=result, download_links=download_links,
                           preview=preview, plots=plots, contributor_data=contributor_data)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['TEMP_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
