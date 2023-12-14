## About 

PyAQ is an open-source reference implementation of the semantic broker, 
a platform for cognitive applications using large language models. 

For more information visit us at https://anyquest.ai

## Installation 

### Operating System 

These instructions were prepared for Linux and MacOS. Some modifications may be required on Windows.

### Python 

PyAQ requires Python 3.10 or 3.11. 

You can check the version of Python installed on your machine by opening a terminal window 
and running 

```
> python3 --version 
```

### Virtual Environment 

Create and activate the virtual Python environment: 

1. Open a terminal window 
2. Change to the directory of this file 
3. Run the following commands at the command prompt 

```
> python -m venv venv 
> source venv/bin/activate
> pip install poetry 
> poetry install --no-root
> pip install jupyter
```

### API Keys

At the root folder of the source tree, create a file named .env containing the following: 

```
OPENAI_API_KEY=<Your OpenAI API key>
ANTHROPIC_API_KEY=<Your Anthropic API key>

AZURE_API_KEY=<Your Azure API key>
AZURE_API_VERSION=<Azure API version>
AZURE_DEPLOYMENT=<Azure Model deployment>
AZURE_ENDPOINT=<Azure endpoint>

GOOGLE_CSE_CX=<Your Google Programmable Search Engine ID>
GOOGLE_CSE_KEY=<Your Google Programmable Search Engine API Key>
```

The OpenAI API key is required since most examples depend on it. 
Google CSE settings are required by the web tool. 
If you do not have Anthropic or Azure API keys, you can still run all 
examples but will need to replace the corresponding models with the 
ones provided by OpenAI. 

## Examples

To run the examples, switch to the examples directory and launch Jupyter: 

```
> cd examples
> jupyter notebook examples.ipynb 
```

You can now run the notebook cells one-by-one starting from the top. 
