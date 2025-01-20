import time
import csv
import re
import os
import shutil
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from deepchecks.tabular import Dataset
from deepchecks.tabular.suites import data_integrity
from deepchecks.tabular.checks.data_integrity import PercentOfNulls
from kaggle.api.kaggle_api_extended import KaggleApi

URL_start = "https://www.kaggle.com/datasets?tags=13302-Classification/"

datasetList_xPath = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul"

title_xPath1 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
title_xPath2 = "]/div[1]/a/div[2]/div"

upvote_xPath1 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
upvote_xPath2 = "]/div[1]/div/div/span"

size_xPath1 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
size_xPath2 = "]/div[1]/a/div[2]/span[2]/text()[4]"

size_xPath3 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
size_xPath4 = "]/div[1]/a/div[2]/span[2]/text()[2]"

usability_xPath1 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
usability_xPath2 = "]/div[1]/a/div[2]/span[2]/span/span"

medal_xPath1 = "//*[@id=\"site-content\"]/div[6]/div/div/div/ul/li["
medal_xPath2 = "]/div[1]/div/span/span/text()"

totalNumberOfPages = 200

if __name__ == "__main__":

    allHeader = ['title', 'upvote', 'size', 'usability', 'medal']

    # open the file in the write mode
    with open('sampleDatasets.csv', 'w', encoding='UTF8') as f:
        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        writer.writerow(allHeader)

    driver = webdriver.Safari()

    for numPage in range(totalNumberOfPages):
        if numPage == 0:
            driver.get(URL_start)
            time.sleep(3)
        else:
            driver.get(URL_start + "&page=" + str(numPage + 1))
            time.sleep(3)

        print("Scraping page " + str(numPage + 1))

        try:
            datasetList = driver.find_element(By.XPATH, datasetList_xPath)
            datasets = datasetList.find_elements(By.TAG_NAME, "li")
            numberPageDatasets = len(datasets)
        except NoSuchElementException:
            numberPageDatasets = 0

        if numberPageDatasets > 0:
            for i in range(numberPageDatasets):
                with open('sampleDatasets.csv', 'a+', encoding='UTF8') as f:
                    writer = csv.writer(f)

                    title = driver.find_element(By.XPATH, title_xPath1 + str(i + 1) + title_xPath2)
                    upvote = driver.find_element(By.XPATH, upvote_xPath1 + str(i + 1) + upvote_xPath2)

                    try:
                        size = driver.find_element(By.XPATH, size_xPath1 + str(i + 1) + size_xPath2)
                    except NoSuchElementException:
                        size = driver.find_element(By.XPATH, size_xPath3 + str(i + 1) + size_xPath4)

                    try:
                        usability = driver.find_element(By.XPATH, usability_xPath1 + str(i + 1) + usability_xPath2)
                        usability = usability.text
                    except NoSuchElementException:
                        usability = ""

                    try:
                        medal = driver.find_element(By.XPATH, medal_xPath1 + str(i + 1) + medal_xPath2)
                        medal = medal.text
                    except NoSuchElementException:
                        medal = ""

                    infoDataset = [title.text, upvote.text, size.text, usability, medal]

                    writer.writerow(infoDataset)
        else:
            break

    df = pd.read_csv("newdatasets/sampleDatasets.csv")

    for i in range(len(df['size'])):
        size = re.findall('[0-9]+', str(df['size'][i]))
        if re.search('kB', str(df['size'][i])) is not None:
            df['size'].replace(to_replace=df['size'][i], value=int(size[0]) * 1e3, inplace=True)
        elif re.search('MB', str(df['size'][i])) is not None:
            df['size'].replace(to_replace=df['size'][i], value=int(size[0]) * 1e6, inplace=True)
        elif re.search('GB', str(df['size'][i])) is not None:
            df['size'].replace(to_replace=df['size'][i], value=int(size[0]) * 1e9, inplace=True)
        elif re.search('B', str(df['size'][i])) is not None:
            df['size'].replace(to_replace=df['size'][i], value=int(size[0]) * 1, inplace=True)

    df.to_csv('newdatasets/allNewDatasets.csv')

    checkedHeader = ['title', 'Data Duplicates',
                     'Feature-Feature Correlation',
                     'Missing Values', 'Mixed Data Types', 'Mixed Nulls', 'Outlier Sample Detection',
                     'Single Value in Column',
                     'Special Characters', 'String Length Out Of Bounds', 'String Mismatch']

    # open the file in the write mode
    with open('newdatasets/checkedDatasets.csv', 'w') as f:
        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        writer.writerow(checkedHeader)

    api = KaggleApi()
    api.authenticate()

    tags = "Classification"
    files = "csv"
    download_datasets_directory = "DownloadDatasetsKaggle"


    def getNullPercentages(str):
        array = re.findall(r'[0-9]+(?:\.[0-9]+)?', str)
        return array


    datasets_with_problems = pd.read_csv('datasets/datasetsWithProblems.csv')
    datasets_with_problems = datasets_with_problems['title'].tolist()

    checkDeepchecks = pd.read_csv('newdatasets/checkedDatasets.csv')
    datasetsnames = checkDeepchecks['title'].tolist()

    for page in range(50):
        print("\nWe are at page number: " + str(page + 1))
        pageRepo = api.dataset_list(tag_ids=tags, file_type=files, page=page + 1)
        for repo in pageRepo:
            print(repo)
            datasetname = re.split('/', str(repo))[-1]
            if datasetname not in datasets_with_problems and datasetname not in datasetsnames:
                datasetsnames.append(datasetname)
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
                        newDataset = ['', '', '', '', '', '', '', '', '', '', '']
                        newDataset[0] = datasetname
                        ds = Dataset(data)
                        integ_suite = data_integrity()
                        suite_result = integ_suite.run(ds, with_display=False)
                        suite_json = suite_result.to_json(with_display=False)
                        nulls_result = PercentOfNulls().run(ds)
                        nulls_json = nulls_result.to_json()
                        print('End checks!')

                        nullNumbers = getNullPercentages(json.loads(nulls_json)['value'])
                        nullSum = 0
                        for i in range(len(nullNumbers)):
                            nullSum += float(nullNumbers[i])
                        nullMean = nullSum / len(nullNumbers)
                        newDataset[3] = nullMean

                        for i in range(len(json.loads(suite_json)["results"])):
                            check = json.loads(suite_json)["results"][i]['check']['name']
                            if check == 'Data Duplicates':
                                try:
                                    newDataset[1] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[1] = ""
                            elif check == 'Feature Feature Correlation':
                                try:
                                    newDataset[2] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[2] = ""
                            elif check == 'Mixed Data Types':
                                try:
                                    newDataset[4] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[4] = ""
                            elif check == 'Mixed Nulls':
                                try:
                                    newDataset[5] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[5] = ""
                            elif check == 'Outlier Sample Detection':
                                try:
                                    outliers = json.loads(suite_json)["results"][8]['value']
                                    mean_outliers = sum(outliers) / len(outliers)
                                    newDataset[6] = mean_outliers
                                except KeyError:
                                    newDataset[6] = ""
                            elif check == 'Is Single Value':
                                try:
                                    newDataset[7] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[7] = ""
                            elif check == 'Special Characters':
                                try:
                                    newDataset[8] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[8] = ""
                            elif check == 'String Length Out Of Bounds':
                                try:
                                    newDataset[9] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[9] = ""
                            elif check == 'String Mismatch':
                                try:
                                    newDataset[10] = json.loads(suite_json)["results"][i]['conditions_results'][0][
                                        'Status']
                                except KeyError:
                                    newDataset[10] = ""
                        checkDeepchecks.loc[len(checkDeepchecks)] = newDataset
                        checkDeepchecks.to_csv('checkDatasets.csv', index=False)
                    if os.path.getsize(filename) >= 5e8:
                        with open('datasetsWithProblems.csv', 'a') as f:
                            print('Dataset with problems: ' + datasetname)
                            f.write(datasetname + '\n')
                            f.close()
                    try:
                        os.remove(filename)
                    except PermissionError:
                        shutil.rmtree(filename, ignore_errors=True)

    checkDeepchecks.to_csv('newdatasets/checkedDatasets.csv', index=False)
