import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import pm4py
import seaborn as sns
import io
import base64
import requests
import os
from sklearn.cluster import DBSCAN

def generate_text_summary(original_data, ocel_data, objects_summary):
    """
    Generate a text summary of the repository data.

    Parameters:
    original_data: pandas dataframe.
    ocel_data: OCEL converted data.
    objects_summary: objects summary of the OCEL data.
    Returns:
    str: A formatted string containing the summary of the repository data.
    """
    get_object_types = pm4py.ocel.ocel_get_object_types(ocel_data)
    get_attribute_names = pm4py.ocel.ocel_get_attribute_names(ocel_data)
    unique_contributors, average_commits_per_contributor = basic_stats(original_data)

    result = f"""Repository processed successfully.
• Data shape: {original_data.shape}
• Number of unique contributors: {unique_contributors}
• Average number of commits per contributor: {average_commits_per_contributor:.2f}
• {len(get_object_types)} object types: {', '.join(get_object_types)}
• {len(get_attribute_names)} attributes: {', '.join(get_attribute_names)}
• Total objects: {len(objects_summary)}
• Objects with lifecycle duration > 0: {len(objects_summary[objects_summary.lifecycle_duration > 0])}"""
    
    return result
           
            
def convert_to_ocel_and_get_summary(data):
    ocel_data = pm4py.convert.convert_log_to_ocel(data,
                                              activity_column = 'ocel:activity',
                                              timestamp_column = 'ocel:timestamp',
                                              object_types = ['ocel:type:files', 'ocel:type:branches', 'ocel:type:author'],
                                              obj_separator = ',',
                                              additional_event_attributes = ['commit_message', 'author_email', 'merge'])
    # ocel_data.event_timestamp = pd.to_datetime(ocel_data.event_timestamp)
    temporal_summary = pm4py.ocel_temporal_summary(ocel_data)
    objects_summary = pm4py.ocel.ocel_objects_summary(ocel_data)
    return ocel_data, temporal_summary, objects_summary


def lifecycle_duration_plot(objects_summary):
    fig = sns.displot(objects_summary.lifecycle_duration)

    # Save plot to a BytesIO object
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig.fig)  # Close the figure to free memory
    buf.seek(0)

    plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    return plot_url


def is_public_github_repo(input_text):
    # Regular expression to match GitHub repository URLs
    github_url_pattern = r'https?://github\.com/[\w-]+/[\w.-]+'

    # Check if the input matches the GitHub URL pattern
    match = re.match(github_url_pattern, input_text)

    if not match:
        return False

    # Extract the API URL for the repository
    api_url = f"https://api.github.com/repos/{input_text.split('github.com/')[1]}"

    try:
        # Send a GET request to the GitHub API
        response = requests.get(api_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            repo_data = response.json()
            # Check if the repository is public
            return not repo_data.get('private', True)
        else:
            return False
    except requests.RequestException:
        return False

def basic_stats(df):
    unique_contributors = df.author_email.nunique()
    average_commits_per_contributor = len(df) / df.author_email.nunique()
    return unique_contributors, average_commits_per_contributor

def generate_plots(df):
    plots = []
    
    # Plot 1: Commits per contributor
    plt.figure(figsize=(10, 6))
    commits_per_contributor = df['ocel:type:author'].value_counts()
    
    if len(commits_per_contributor) >= 20:
        top_contributors = commits_per_contributor.nlargest(20)
        top_contributors.plot(kind='bar')
        plt.title('Top 20 Contributors by Commits')
    else:
        commits_per_contributor.plot(kind='bar')
        plt.title('Commits per Contributor')
    
    plt.xlabel('Contributor')
    plt.ylabel('Number of Commits')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plots.append(get_plot_url())

    # Plot 2: Commits over time
    plt.figure(figsize=(10, 6))
    # Ensure 'ocel:timestamp' is datetime and set it as index
    df['ocel:timestamp'] = pd.to_datetime(df['ocel:timestamp'], utc=True)
    df = df.set_index('ocel:timestamp').sort_index()
    df.resample('W')['ocel:eid'].count().plot()
    plt.title('Commits Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Commits')
    plt.tight_layout()
    plots.append(get_plot_url())

    return plots

def get_plot_url():
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return plot_url

def generate_ocdfg(ocel_data, filepath):
    ocdfg = pm4py.ocel.discover_ocdfg(ocel_data)
    
    # Increase the DPI (dots per inch) for higher resolution
    # Adjust the figure size for a larger image
    # Set a white background to ensure clarity
    pm4py.save_vis_ocdfg(ocdfg, filepath, 
                         annotation='frequency',
                         bgcolor="white",
                         dpi=300,
                         figsize=(20, 16))

def generate_ocpn(ocel_data, filepath):
    # Discover the Object-Centric Petri Net from the OCEL data
    ocpn = pm4py.discover_oc_petri_net(ocel_data)
    
    # Increase the DPI (dots per inch) for higher resolution
    # Adjust the figure size for a larger image
    # Set a white background to ensure clarity
    pm4py.save_vis_ocpn(ocpn, filepath, 
                        parameters={
                            "bgcolor": "white",
                            "format": "png",
                            "dpi": 300,
                            "figsize": (20, 16)
                        })


def contributor_analysis(data):
    # Count the number of commits per contributor
    commits_per_contributor = data['author_email'].value_counts()

    # Get the top 5 contributors
    top_contributors = commits_per_contributor.head(5)

    originator_by_task_matrix = pd.pivot_table(data, 
                                           values='ocel:eid', 
                                           index=['author_email'],
                                           columns=['ocel:activity'], 
                                           aggfunc="count",
                                           fill_value=0)
    
    matrix_df = pd.DataFrame(originator_by_task_matrix)
    clustering = DBSCAN().fit(matrix_df)
    labels = clustering.labels_

    # Generate the histogram plot
    plt.figure(figsize=(10, 6))
    fig = sns.histplot(labels, kde=False)
    plt.title('Contributor Clustering')
    plt.xlabel('Cluster Label')
    plt.ylabel('Number of Contributors')
    
    # Save plot to a BytesIO object
    buf = io.BytesIO()
    fig.figure.savefig(buf, format='png')
    plt.close(fig.figure)  # Close the figure to free memory
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Create the cluster summary table
    cluster_summary = []
    all_authors = []
    
    # Sort cluster labels to ensure desired order
    sorted_cluster_labels = sorted(set(labels), key=lambda x: (x != -1, x))
    
    for cluster_id in sorted_cluster_labels:
        if cluster_id == -1:
            cluster_name = "Most Active Contributors"
        else:
            cluster_name = f"Cluster {cluster_id}"
        
        cluster_authors = matrix_df.index[labels == cluster_id].tolist()
        cluster_data = data[data['author_email'].isin(cluster_authors)]
        
        total_commits = cluster_data.shape[0]
        total_files = cluster_data['ocel:type:files'].str.split(',').explode().nunique()
        avg_files_per_author = cluster_data.groupby('author_email')['ocel:type:files'].apply(lambda x: x.str.split(',').explode().nunique()).mean()
        
        avg_commits = total_commits / len(cluster_authors) if cluster_authors else 0
        
        cluster_summary.append({
            'Cluster ID': cluster_name,
            'Number of Authors': len(cluster_authors),
            'Total Commits': total_commits,
            'Average Commits': avg_commits,
            'Total Files Edited': total_files,
            'Avg Files per Author': avg_files_per_author
        })
        
        all_authors.extend([(author, cluster_name, avg_commits) for author in sorted(cluster_authors)])

    cluster_summary_df = pd.DataFrame(cluster_summary)
    
    # Format numeric columns
    cluster_summary_df['Average Commits'] = cluster_summary_df['Average Commits'].apply(lambda x: f"{x:.2f}")
    cluster_summary_df['Avg Files per Author'] = cluster_summary_df['Avg Files per Author'].apply(lambda x: f"{x:.2f}")

    # Sort all_authors list by cluster order, then by author name
    all_authors.sort(key=lambda x: (sorted_cluster_labels.index(int(x[1].split()[-1]) if x[1] != "Most Active Contributors" else -1), x[0]))
    all_authors = [f"{author} ({cluster})" for author, cluster, _ in all_authors]

    return {
        'top_contributors': top_contributors.to_dict(),
        'cluster_plot': plot_url,
        'cluster_summary': cluster_summary_df.to_dict('records'),
        'all_authors': all_authors
    }
