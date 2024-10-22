import argparse
from functional import is_public_github_repo, basic_stats, generate_ocdfg, convert_to_ocel_and_get_summary
from repo_parser import process_github_repo
from label_classific import predict

def process_repository(user_input, is_conventional_standard):
    if is_public_github_repo(user_input):
        df, branches_map = process_github_repo(user_input, conventional_commits=is_conventional_standard)
        if not is_conventional_standard:
            df['ocel:activity'] = [predict(message) for message in df['commit_message']]
        
        # Save data.csv
        filename = 'data.csv'
        df.to_csv(filename, index=False)
        
        # Generate ocdfg.png
        ocel_data, _, _ = convert_to_ocel_and_get_summary(df)
        ocdfg_filename = generate_ocdfg(ocel_data)
        
        unique_contributors, average_commits_per_contributor = basic_stats(df)
        
        result = f"Repository processed successfully. Data shape: {is_conventional_standard}. \n " \
                 f"Number of unique contributors: {unique_contributors}. " \
                 f"Average number of commits per contributor: {average_commits_per_contributor}. "
        
        return result, filename, ocdfg_filename
    else:
        return "The input is not a valid GitHub link to a public repository.", None, None

def main():
    parser = argparse.ArgumentParser(description='Debug Flask App Backend')
    parser.add_argument('user_input', type=str, help='GitHub repository URL')
    parser.add_argument('--conventional', action='store_true', help='Use conventional commits standard')
    
    args = parser.parse_args()
    
    result, data_file, ocdfg_file = process_repository(args.user_input, args.conventional)
    print(result)
    if data_file and ocdfg_file:
        print(f"Data saved to {data_file}")
        print(f"OCDFG image saved to {ocdfg_file}")

if __name__ == '__main__':
    main()
