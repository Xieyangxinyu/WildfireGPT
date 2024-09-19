# WildfireGPT: Tailored  Large Language Model for Wildfire Analysis

## Pre-requisites
We use Python 3.11.6 and [Poetry](https://python-poetry.org/) to manage dependencies. 

We recommend using [pyenv](https://github.com/pyenv/pyenv) to manage your python versions. To switch to Python 3.11.6, run 
```
pyenv install 3.11.6
pyenv local 3.11.6
```

To After pulling from github, in your ``callm`` folder, do the following to install the dependencies:
```
poetry build
poetry install # install dependencies
poetry shell # make a virtual environment
```

If you would like to exit the virtual environment, run
```
exit # exit shell
```

Lastly, create a ``.env`` file in the root directory of the project and add the following:
```
OPENAI_API_KEY=<your openai api key>
model=<your model name  # e.g. gpt-4-1106-preview>
```
Please check [OpenAI Model Pricing](https://openai.com/pricing) before choosing a model.

All data are available under the ``data`` folder. You can download all the data from this [Box Link](https://anl.box.com/s/wm888zovyapyou1txae7g75ghpc7sxre).

## Data

- The Fire Weather Index (FWI) projections from ClimRR are available for download at [https://anl.app.box.com/s/hmkkgkrkzxxocfe9kpgrzk2gfc4gizp8](https://anl.app.box.com/s/hmkkgkrkzxxocfe9kpgrzk2gfc4gizp8). Make sure to include `GridCellsShapefile` as well as `FireWeatherIndex_Wildfire.csv`.
- Wildland Fire Incident Locations data can be accessed at [https://data-nifc.opendata.arcgis.com/datasets/nifc::wildland-fire-incident-locations/about](https://data-nifc.opendata.arcgis.com/datasets/nifc::wildland-fire-incident-locations/about). To run WildfireGPT, we pruned the data to include these four columns: `lon`, `lat`, `year`, `month` and renamed the file to `data/Wildland_Fire_Incident_Locations_pruned.csv`.
- The North American Tree-Ring Fire Scar Synthesis (NAFSS) dataset can be downloaded from [https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=noaa-fire-34853](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=noaa-fire-34853). 
- Census ACS5 data is accessible via the Python API package at [https://github.com/Census-ACS/census](https://github.com/Census-ACS/census). 
- The scientific literature data developed by CIACC can be downloaded from [https://anl.box.com/s/b4m2mnt5wa4z9l71qioz05cb5qpduj2j](https://anl.box.com/s/b4m2mnt5wa4z9l71qioz05cb5qpduj2j). To create the embedding and index, run 

```
python src/literature/embedding.py
python src/literature/index.py
```

## Run WildfireGPT
We use [Streamlit](https://streamlit.io) to create a web app. To run the web app, run
```
streamlit run src/wildfireChat.py
```

## Evaluate the Case Study Results

To evaluate the case study results, run
```
python src/evaluation/eval_offline.py
```
This will generate the GPT-as-Judge evaluation results under each case study folder. To compute the domain expert evaluation scores,
```
python src/evaluation/extract_expert_score.py
```