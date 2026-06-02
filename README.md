# Long-Form Factuality in Large Language Models

This is the official code release accompanying our paper ["Long-form factuality in large language models"](https://arxiv.org/abs/2403.18802).
This repository contains:

1. **LongFact**: A prompt set of 2,280 fact-seeking prompts requiring long-form responses.
2. **Search-Augmented Factuality Evaluator (SAFE)**: Automatic evaluation of model responses in long-form factuality settings.
3. **F1@K**: Extending F1 score to long-form settings using recall from human-preferred length.
4. **Experimentation pipeline** for benchmarking OpenAI and Anthropic models using LongFact + SAFE.

## Installation

First, clone our GitHub repository.

```bash
git clone https://github.com/google-deepmind/long-form-factuality.git
```

Then navigate to the newly-created folder.
```bash
cd long-form-factuality
```

Next, create a new Python 3.10+ environment using `conda`.

```bash
conda create --name longfact python=3.10
```

Activate the newly-created environment.

```bash
conda activate longfact
```

All external package requirements are listed in `requirements.txt`.
To install all packages, and run the following command.

```bash
pip install -r requirements.txt
```

### llm_uncertainty workspace fork

This checkout is used as an external LongFact/SAFE baseline inside
`/home/elp/project/llm_uncertainty`. Run local checks and SAFE jobs in the
isolated environment:

```bash
conda run -n llm_uq_longfact python ...
```

Important local changes:

- `common/shared_config.py` loads the project `.env` and supports
  OpenAI-compatible evaluator endpoints. Evaluator credentials are read from
  `LONGFACT_OPENAI_API_KEY`, `CODEXAPIS_API_KEY`, `OPENAI_API_KEY`, or
  `GPTGOD_API_KEY`; evaluator base URLs are read from
  `LONGFACT_OPENAI_BASE_URL`, `CODEXAPIS_BASE_URL`, `OPENAI_API_BASE`,
  `OPENAI_BASE_URL`, or `GPTGOD_BASE_URL`. The default evaluator model is
  `LONGFACT_OPENAI_MODEL`, `CODEXAPIS_EXTRACTOR_MODEL`, or `OPENAI_MODEL`,
  falling back to `gpt-5.4-mini`.
- SAFE search credentials are separate from evaluator credentials. For
  OpenAI-compatible web search, set `LONGFACT_SEARCH_OPENAI_API_KEY`,
  `LONGFACT_SEARCH_OPENAI_BASE_URL`, and optionally
  `LONGFACT_SEARCH_OPENAI_MODEL`. If they are unset, the search wrapper falls
  back to the evaluator key/base URL/model for backward compatibility.
- `eval/safe/rate_atomic_fact.py` supports `serper`, `brave`, and `openai_web`.
  The current workspace default for LongFact evaluation is intended to be
  `LONGFACT_SAFE_SEARCH_TYPE=openai_web` with `gpt-5.4-mini`. This is
  SAFE-style LLM web search, not the original paper's Serper-backed SAFE.
- The repository still pins `openai==0.27.2`. The evaluator uses the old
  ChatCompletion interface, while `openai_web` calls the Responses
  `/responses` endpoint through `requests`, so no OpenAI SDK upgrade is needed
  for the current wrapper.

## Usage
### LongFact
The full prompt set for LongFact is available in the `longfact/` folder.
See the README in `longfact/` for more details about the dataset.

To run the data-generation pipeline that we used to generate LongFact, use the following command.
Refer to the README in `data_creation/` for additional details about the data-generation pipeline.

```bash
python -m data_creation.pipeline
```

### SAFE
Our full implementation of SAFE is located in `eval/safe/`.
See the README in `eval/safe/` for more information about how SAFE works.

To run the pipeline for evaluating SAFE against FActScore human annotations, use the following command.
Refer to the README in `eval/` for additional details about this experiment.

```bash
python -m eval.correlation_vs_factscore
```

### Benchmarking models
To benchmark OpenAI and Anthropic models, first add your API keys to `common/shared_config.py` (see README in `common/` for more information; be sure not to publish these keys).
To obtain model responses for a given prompt set, use the following command.
Refer to the README in `main/` for additional details about our main experimentation pipeline.

```bash
python -m main.pipeline
```

Next, to evaluate prompt-response pairs from our main experimentation pipeline using SAFE, use the following command, making sure to add the path to the `.json` file containing the prompt-response pairs to be evaluated to the `--result_path` argument.

```bash
python -m eval.run_eval \
    --result_path=
```

## Unit Tests

Each file in this directory has a corresponding unit test with the `_test` suffix (e.g., `file.py` would have `file_test.py` for unit tests).
Run commands for individual tests are shown in the unit test files.
To run all unit tests, use the following command.

```bash
python -m unittest discover -s ./ -p "*_test.py"
```

## Citing this work

If you find our code useful, please cite our [paper](https://arxiv.org/abs/2403.18802):

```bibtex
@misc{wei2024long,
  title={Long-form factuality in large language models},
  author={Wei, Jerry and Yang, Chengrun and Song, Xinying and Lu, Yifeng and Hu, Nathan and Huang, Jie and Tran, Dustin and Peng, Daiyi and Liu, Ruibo and Huang, Da and Du, Cosmo and Le, Quoc V.},
  year={2024},
  url={https://arxiv.org/abs/2403.18802},
}
```

## License and disclaimer

Copyright 2024 DeepMind Technologies Limited

All software is licensed under the Apache License, Version 2.0 (Apache 2.0);
you may not use this file except in compliance with the Apache 2.0 license.
You may obtain a copy of the Apache 2.0 license at:
https://www.apache.org/licenses/LICENSE-2.0

All other materials are licensed under the Creative Commons Attribution 4.0
International License (CC-BY). You may obtain a copy of the CC-BY license at:
https://creativecommons.org/licenses/by/4.0/legalcode

Unless required by applicable law or agreed to in writing, all software and
materials distributed here under the Apache 2.0 or CC-BY licenses are
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the licenses for the specific language governing
permissions and limitations under those licenses.

This is not an official Google product.
