# SQUALO - dataSets QUality Analysis and Labelling Operations
## Introduction

High-quality data is the cornerstone of successful machine learning models, yet many practitioners bypass the vital step of performing data quality checks. Addressing this gap, our research introduces an automated approach to conduct data quality assessments on tabular data, a common resource in machine learning pipelines.

## Methodology

Leveraging a subset of pivotal metrics for machine learning pipelines, we built a system to perform data quality evaluations automatically. Deepchecks served as our primary tool in this endeavor, with its efficacy tested against other notable data quality tools from both the academic and industry arenas.

Our methodology involved:
- Identification and use of a subset of crucial metrics for machine learning pipelines
- Harnessing the Deepchecks tool and contrasting its performance with other renowned data quality tools
- Applying the proposed system to various tabular datasets derived from Kaggle
- Analysing the core features employed by Kaggle to rank datasets, utilizing them to verify the applicability of our approach

## Results

The results underscored the substantial potential of automated data quality checks in enhancing both the efficiency and reliability of machine learning pipelines. Our approach mitigates the risks of embedding errors and biases into machine learning models, thereby promising more robust outcomes.

## Datasets

We analyzed a series of tabular datasets obtained from Kaggle in May 2023. These datasets, alongside our analysis scripts, can be found in the `datasets/` and `scripts/` folders, respectively.

## Installation

To set up the repository locally, execute the following command:

```sh
git clone https://github.com/MatteoPancini/SQUALO.git
```

## Usage

Users have two options for engaging with our research:

1. **Replicating the Original Experiment** (with data from May 2023): To replicate our experiment with the original dataset, use the following command:
   
   ```sh
   python3 replicate_experiment.py
    ```
   
2. **Running the Experiment with New Data**: To run our experiment with new data, use the following command:
   - **Step 1**: Download the new data from Kaggle and save it in the `newdatasets/` folder:
   ```sh
   python3 download_new_dataset.py
    ```
   - **Step 2**: Run the following command to compare the new data with the original dataset:
    ```sh
      python3 run_new_experiment.py
    ```


