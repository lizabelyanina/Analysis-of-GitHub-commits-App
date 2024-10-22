from pydriller import Repository
import pandas as pd

def process_github_repo(repo_url, conventional_commits=False):
    timestamps = []
    hashes = []
    activities = []
    messages = []
    authors_names = []
    authors_emails = []
    merge_yns = []
    files = []
    branches = []
    total_branches = set()
    total_files = set()
    branches_counter = 0
    branches_map = dict()

    for commit in Repository(repo_url).traverse_commits():
        try:
            # Convert author_date to datetime and append to timestamps
            timestamp = pd.to_datetime(commit.author_date, errors='coerce', utc=True)
            if pd.isnull(timestamp):
                print(f"Warning: Invalid date encountered in commit {commit.hash}")
            timestamps.append(timestamp)
        except Exception as e:
            print(f"Error processing commit {commit.hash}: {e}")
            timestamps.append(pd.NaT)  # Append Not a Time for problematic entries

        hashes.append(commit.hash)

        if conventional_commits:
            activities.append(commit.msg.split(' ')[0].split('(')[0].replace(':', '').lower())

        messages.append(commit.msg.replace(',', ''))
        authors_names.append(commit.author.name)
        authors_emails.append(commit.author.email)
        merge_yns.append(commit.merge)

        try:
            files.append("[" + ", ".join(["'" + str(file.new_path) + "'" for file in commit.modified_files]) + "]")
            total_files.update([str(file.new_path) for file in commit.modified_files])
        except:
            files.append("[]")

        branches_mapped = []
        for branch in commit.branches:
            if str(branch) not in branches_map:
                branches_map[str(branch)] = str(branches_counter)
                branches_counter += 1
            branches_mapped.append(branches_map[str(branch)])
        branches.append("[" + ", ".join(["'" + branch_mapped + "'" for branch_mapped in branches_mapped]) + "]")
        total_branches.update([str(branch) for branch in commit.branches])

    if conventional_commits:
        df = pd.DataFrame({
            'ocel:timestamp': timestamps, 
            'ocel:eid': hashes, 
            'ocel:activity': activities, 
            'commit_message': messages,
            'ocel:type:author': authors_names, 
            'author_email': authors_emails, 
            'merge': merge_yns,
            'ocel:type:files': files, 
            'ocel:type:branches': branches
        })
    else:
        df = pd.DataFrame({
            'ocel:timestamp': timestamps, 
            'ocel:eid': hashes, 
            'ocel:activity': messages, 
            'commit_message': messages, 
            'ocel:type:author': authors_names, 
            'author_email': authors_emails, 
            'merge': merge_yns, 
            'ocel:type:files': files,
            'ocel:type:branches': branches
        })

    return df, branches_map

# Example usage in your Flask app:
# from your_script import process_github_repo

# @app.route('/process_repo', methods=['POST'])
# def process_repo():
#     repo_url = request.form.get('repo_url')
#     conventional_commits = request.form.get('conventional_commits', False)
#     df, branches_map = process_github_repo(repo_url, conventional_commits)
#
#     # Process the DataFrame and branches_map as needed
#     # You can return the results as JSON, render a template, etc.
#     return jsonify({'success': True, 'data': df.to_dict(), 'branches_map': branches_map})

# df, branches_map = process_github_repo("https://github.com/haunt98/changeloguru", conventional_commits=True)
#
# print(df)
