import pandas as pd
import numpy as np

# Function to print the analysis of the dataset
def print_analysis(dataset, analysis_type):
    print(f"\n{'*' * 20} {analysis_type} Analysis {'*' * 20}\n")
    print(dataset.describe())

    for col in status_cols:
        value_counts = dataset[col].value_counts(normalize=True)  # Normalize=True gives the relative frequencies
        print(f"\nColumn: {col}")
        print(f"{'FAIL':<5}: {value_counts.get('FAIL', 0) * 100:5.2f}%")
        print(f"{'WARN':<5}: {value_counts.get('WARN', 0) * 100:5.2f}%")
        print(f"{'PASS':<5}: {value_counts.get('PASS', 0) * 100:5.2f}%")

# Read the datasets
allDatasets = pd.read_csv('datasets/allDatasets.csv')
checkedDatasets = pd.read_csv('datasets/checkedDatasets.csv')

# Map the status to numbers
status_mapping = {'PASS': 1, 'WARN': 2, 'FAIL': 3}
reverse_mapping = {v: k for k, v in status_mapping.items()}

# List of status and value columns
status_cols = ['Data Duplicates', 'Feature-Feature Correlation', 'Mixed Data Types',
               'Mixed Nulls', 'Single Value in Column',
          'Special Characters', 'String Length Out Of Bounds', 'String Mismatch']
numeric_cols = ['Missing Values', 'Outlier Sample Detection']

# Loop over status columns
for col in status_cols:
    checkedDatasets[f'{col}_num'] = checkedDatasets[col].map(status_mapping)
    checkedDatasets[f'{col}_num'] = checkedDatasets.groupby('title')[f'{col}_num'].transform(max)
    checkedDatasets[col] = checkedDatasets[f'{col}_num'].map(reverse_mapping)
    checkedDatasets = checkedDatasets.drop(f'{col}_num', axis=1)

# Loop over value columns
for col in numeric_cols:
    checkedDatasets[col] = checkedDatasets.groupby('title')[col].transform(np.mean)

# Drop duplicates
checkedDatasets = checkedDatasets.drop_duplicates('title')

# Merge of the two dataframes
finalDataset = pd.merge(allDatasets, checkedDatasets, on='title', how='inner')


# Hotness Analysis
hotness = finalDataset.head(100)
print_analysis(hotness, "Hotness")

# Most Votes Analysis
mostVotes = finalDataset.sort_values(by=['upvote'], ascending=False).head(100)
print_analysis(mostVotes, "Most Votes")

# Usability Analysis
usability = finalDataset.sort_values(by=['usability'], ascending=False).head(100)
print_analysis(usability, "Usability")