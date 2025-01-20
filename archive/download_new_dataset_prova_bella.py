import os
import re
import csv
import time
import shutil
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from shutil import rmtree
from deepchecks.tabular import Dataset
from deepchecks.tabular.suites import data_integrity
from deepchecks.tabular.checks.data_integrity import PercentOfNulls
import json
from kaggle.api.kaggle_api_extended import KaggleApi


def initialize_csv(filepath, headers):
    with open(filepath, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)


def get_web_elements(driver, base_xpath, offset_xpath, index):
    try:
        element = driver.find_element(By.XPATH, base_xpath + str(index) + offset_xpath)
        return element.text
    except NoSuchElementException:
        return ""


def write_to_csv(filename, row_data):
    with open(filename, 'a+', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(row_data)


def scrape_kaggle_datasets(driver, start_url, num_pages, xpath_config, csv_filename):
    initialize_csv(csv_filename, ['title', 'upvote', 'size', 'usability', 'medal'])

    for numPage in range(num_pages):
        driver.get(start_url if numPage == 0 else f"{start_url}&page={numPage + 1}")
        time.sleep(3)

        try:
            dataset_list = driver.find_element(By.XPATH, xpath_config['datasetList'])
            datasets = dataset_list.find_elements(By.TAG_NAME, "li")
            num_datasets = len(datasets)
        except NoSuchElementException:
            num_datasets = 0

        for i in range(num_datasets):
            title = get_web_elements(driver, xpath_config['title'][0], xpath_config['title'][1], i + 1)
            upvote = get_web_elements(driver, xpath_config['upvote'][0], xpath_config['upvote'][1], i + 1)
            size = get_web_elements(driver, xpath_config['size'][0], xpath_config['size'][1],
                                    i + 1) or get_web_elements(driver, xpath_config['size'][2], xpath_config['size'][3],
                                                               i + 1)
            usability = get_web_elements(driver, xpath_config['usability'][0], xpath_config['usability'][1], i + 1)
            medal = get_web_elements(driver, xpath_config['medal'][0], xpath_config['medal'][1], i + 1)
            write_to_csv(csv_filename, [title, upvote, size, usability, medal])


def convert_size(df):
    for i in range(len(df['size'])):
        size = re.findall('[0-9]+', str(df['size'][i]))
        size_multiplier = {'kB': 1e3, 'MB': 1e6, 'GB': 1e9, 'B': 1}.get(
            re.search('kB|MB|GB|B', str(df['size'][i])).group(), 1)
        df['size'].replace(to_replace=df['size'][i], value=int(size[0]) * size_multiplier, inplace=True)


def getNullPercentages(str):
    array = re.findall(r'[0-9]+(?:\.[0-9]+)?', str)
    return array

def get_null_percentages(s):
    return [float(x) for x in re.findall(r'[0-9]+(?:\.[0-9]+)?', s)]


def handle_dataset_parsing_error(dataset_name, filename):
    with open('datasetsWithProblems.csv', 'a') as f:
        print(f'Dataset with problems: {dataset_name}')
        f.write(f'{dataset_name}\n')
    try:
        os.remove(filename)
    except PermissionError:
        rmtree(filename, ignore_errors=True)


def parse_json_results(datasetname, suite_json, nulls_json):
    new_dataset = ['', '', '', '', '', '', '', '', '', '', '']
    new_dataset[0] = datasetname

    nullNumbers = getNullPercentages(json.loads(nulls_json)['value'])
    nullSum = 0
    for i in range(len(nullNumbers)):
        nullSum += float(nullNumbers[i])
    nullMean = nullSum / len(nullNumbers)
    new_dataset[3] = nullMean

    for i in range(len(json.loads(suite_json)["results"])):
        check = json.loads(suite_json)["results"][i]['check']['name']
        if check == 'Data Duplicates':
            try:
                new_dataset[1] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[1] = ""
        elif check == 'Feature Feature Correlation':
            try:
                new_dataset[2] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[2] = ""
        elif check == 'Mixed Data Types':
            try:
                new_dataset[4] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[4] = ""
        elif check == 'Mixed Nulls':
            try:
                new_dataset[5] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[5] = ""
        elif check == 'Outlier Sample Detection':
            try:
                outliers = json.loads(suite_json)["results"][8]['value']
                mean_outliers = sum(outliers) / len(outliers)
                new_dataset[6] = mean_outliers
            except KeyError:
                new_dataset[6] = ""
        elif check == 'Is Single Value':
            try:
                new_dataset[7] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[7] = ""
        elif check == 'Special Characters':
            try:
                new_dataset[8] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[8] = ""
        elif check == 'String Length Out Of Bounds':
            try:
                new_dataset[9] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[9] = ""
        elif check == 'String Mismatch':
            try:
                new_dataset[10] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                    'Status']
            except KeyError:
                new_dataset[10] = ""

    return new_dataset


def main():
    URL_START = "https://www.kaggle.com/datasets?tags=13302-Classification/"
    XPATH_CONFIG = {
        'datasetList': "//*[@id=\"site-content\"]/div[6]/div/div/div/ul",
        'title': ["//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/a/div[2]/div"],
        'upvote': ["//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/div/div/span"],
        'size': [
            "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/a/div[2]/span[2]/text()[4]",
            "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/a/div[2]/span[2]/text()[2]"
        ],
        'usability': ["//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/a/div[2]/span[2]/span/span"],
        'medal': ["//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li[", "]/div[1]/div/span/span/text()"]
    }

    CSV_FILENAME = 'newdatasets/sampleDatasets.csv'

    driver = webdriver.Safari()
    scrape_kaggle_datasets(driver, URL_START, 200, XPATH_CONFIG, CSV_FILENAME)

    df = pd.read_csv("newdatasets/sampleDatasets.csv")
    convert_size(df)
    df.to_csv('newdatasets/allNewDatasets.csv')

    checked_header = ['title', 'Data Duplicates', 'Feature-Feature Correlation', 'Missing Values',
                      'Mixed Data Types', 'Mixed Nulls', 'Outlier Sample Detection',
                      'Single Value in Column', 'Special Characters',
                      'String Length Out Of Bounds', 'String Mismatch']

    initialize_csv('newdatasets/checkedDatasets.csv', checked_header)

    api = KaggleApi()
    api.authenticate()
    tags = "Classification"
    files = "csv"
    download_datasets_directory = "DownloadDatasetsKaggle"
    num_kaggle_pages_to_check = 5
    print(num_kaggle_pages_to_check)


    # Load problematic datasets and previously checked datasets
    datasets_with_problems = pd.read_csv('datasets/datasetsWithProblems.csv')['title'].tolist()
    check_deepchecks = pd.read_csv('newdatasets/checkedDatasets.csv')
    datasets_names = check_deepchecks['title'].tolist()

    for page in range(num_kaggle_pages_to_check):
        print("\nWe are at page number: " + str(page + 1))
        pageRepo = api.dataset_list(tag_ids=tags, file_type=files, page=page + 1)
        for repo in pageRepo:
            print(repo)
            datasetname = re.split('/', str(repo))[-1]
            if datasetname not in datasets_with_problems and datasetname not in datasets_names:
                datasets_names.append(datasetname)
                print('Downloading...')
                api.dataset_download_files(str(repo), path=download_datasets_directory, unzip=True)
                print('Downloaded')
                for dataset in os.listdir(download_datasets_directory):
                    filename = str(download_datasets_directory + '/' + str(dataset))
                    if not dataset.startswith('.') and os.path.getsize(filename) < 5e8:
                        if filename.endswith('.csv'):
                            try:
                                try:
                                    data = pd.read_csv(filename, encoding='utf-8')
                                except pd.errors.ParserError:
                                    with open('datasetsWithProblems.csv', 'a') as f:
                                        print('Dataset with problems: ' + datasetname)
                                        f.write(datasetname + '\n')
                                        f.close()
                                    try:
                                        os.remove(filename)
                                    except PermissionError:
                                        shutil.rmtree(filename, ignore_errors=True)
                                    continue
                            except UnicodeDecodeError:
                                data = pd.read_csv(filename, encoding='latin-1')
                        elif filename.endswith('.xlsx'):
                            data = pd.read_excel(filename)


                        ds = Dataset(data)
                        integ_suite = data_integrity()
                        suite_result = integ_suite.run(ds, with_display=False)
                        suite_json = suite_result.to_json(with_display=False)
                        nulls_result = PercentOfNulls().run(ds)
                        nulls_json = nulls_result.to_json()
                        print('End checks!')

                        newDataset = parse_json_results(datasetname, suite_json, nulls_json)
                        check_deepchecks.loc[len(check_deepchecks)] = newDataset
                        check_deepchecks.to_csv('checkDatasets.csv', index=False)

                    if os.path.getsize(filename) >= 5e8:
                        with open('datasetsWithProblems.csv', 'a') as f:
                            print('Dataset with problems: ' + datasetname)
                            f.write(datasetname + '\n')
                            f.close()
                    try:
                        os.remove(filename)
                    except PermissionError:
                        shutil.rmtree(filename, ignore_errors=True)

    check_deepchecks.to_csv('newdatasets/checkedDatasets.csv', index=False)

if __name__ == "__main__":
    main()
