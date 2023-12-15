## About 

PyAQ is an open-source reference implementation of the semantic broker, 
a low-code platform for [cognitive applications](https://www.anyquest.ai/blog/cognitive-applications-and-semantic-brokers/) 
using large language models. 

Unlike interactive GPT chatbots and copilots, cognitive applications can run entirely unattended. 
They do not sacrifice precision for speed and can run longer to process more data, use different types 
of larger AI models, or launch long-running jobs via connected enterprise applications and robotic systems.

Make sure to check out sample apps in the examples/apps directory:

- enrich.yml - enrich sales leads by searching the web
- extract.yml - extract contact information from emails
- investments.yml - generate investment advice based on a market report
- rag.yml - answer a question using information in a pdf document
- qna.yml - answer multiple questions by spawning several workers

For more information visit us at https://anyquest.ai.

By releasing AnyQuest PyAQ as open source, we hope to stimulate innovation in the broader generative AI community. 
Until now, the focus of the community has been on building bigger and better models. 
But models do not deliver value. Value is delivered by applications enabled by these models.

Here are just some ideas to explore with AnyQuest PyAQ:

- Cognitive applications
    - Knowledge management
    - Question answering
    - Hyper personalization
    - Intelligent automation
    - Idea generation and research
- Platform extensions
    - Models: open-source, edge AI
    - Tools: connectors to CRM, ERP, supply chains, marketing automation, etc.
    - Tasks: multi-modal primitives for video, audio, and images.
    - Memory: structured data, flat files, cloud storage
- Tools
    - No-code cognitive application designers
    - Cognitive application copilots
    - Prompt engineering and rewriting
    - Verification, validation, and security of cognitive apps
    - LLM operations
    - Performance optimization and parallelism


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
or 
```
> python --version 
```

### Virtual Environment 

Create and activate the virtual Python environment: 

1. Open a terminal window 
2. Change to the directory of this file 
3. Run the following commands at the command prompt 

Linux or Mac: 

```
> python -m venv venv 
> source venv/bin/activate
> pip install poetry 
> poetry install --no-root
> pip install jupyter
```

Windows: 

```
> python -m venv venv 
> venv\Scripts\activate
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
