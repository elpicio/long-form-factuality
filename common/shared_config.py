# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared configuration across all project code."""

import os

PROJECT_ROOT = os.environ.get("LLM_UNCERTAINTY_ROOT", "/home/elp/project/llm_uncertainty")


def _load_project_env() -> None:
  env_path = os.path.join(PROJECT_ROOT, ".env")
  if not os.path.exists(env_path):
    return

  with open(env_path) as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue
      key, value = line.split("=", 1)
      key = key.strip()
      value = value.strip().strip("'").strip('"')
      if key and key not in os.environ:
        os.environ[key] = value


def _first_env(*names: str) -> str:
  for name in names:
    value = os.environ.get(name)
    if value:
      return value
  return ''


_load_project_env()


################################################################################
#                         FORCED SETTINGS, DO NOT EDIT
# prompt_postamble: str = The postamble to seek more details in output.
# openai_api_key: str = OpenAI-compatible evaluator API key.
# openai_search_api_key: str = OpenAI-compatible web-search API key.
# anthropic_api_key: str = Anthropic API key.
# serper_api_key: str = Serper API key.
# random_seed: int = random seed to use across codebase.
# model_options: Dict[str, str] = mapping from short model name to full name.
# model_string: Dict[str, str] = mapping from short model name to saveable name.
# task_options: Dict[str, Any] = mapping from short task name to task details.
# root_dir: str = path to folder containing all files for this project.
# path_to_data: str = directory storing task information.
# path_to_result: str = directory to output results.
################################################################################
prompt_postamble = """\
Provide as many specific details and examples as possible (such as names of \
people, numbers, events, locations, dates, times, etc.)
"""
openai_api_key = _first_env(
    "LONGFACT_OPENAI_API_KEY",
    "CODEXAPIS_API_KEY",
    "OPENAI_API_KEY",
    "GPTGOD_API_KEY",
)
openai_base_url = _first_env(
    "LONGFACT_OPENAI_BASE_URL",
    "CODEXAPIS_BASE_URL",
    "OPENAI_API_BASE",
    "OPENAI_BASE_URL",
    "GPTGOD_BASE_URL",
)
openai_search_api_key = _first_env(
    "LONGFACT_SEARCH_OPENAI_API_KEY",
    "LONGFACT_OPENAI_WEB_SEARCH_API_KEY",
    "OPENAI_SEARCH_API_KEY",
)
openai_search_base_url = _first_env(
    "LONGFACT_SEARCH_OPENAI_BASE_URL",
    "LONGFACT_OPENAI_WEB_SEARCH_BASE_URL",
    "OPENAI_SEARCH_BASE_URL",
)
anthropic_api_key = ''
serper_api_key = _first_env("SERPER_API_KEY", "LONGFACT_SERPER_API_KEY")
brave_search_api_key = _first_env("BRAVE_SEARCH_API_KEY", "LONGFACT_BRAVE_SEARCH_API_KEY")
default_openai_model = _first_env(
    "LONGFACT_OPENAI_MODEL",
    "CODEXAPIS_EXTRACTOR_MODEL",
    "OPENAI_MODEL",
) or "gpt-5.4-mini"
openai_web_search_model = _first_env(
    "LONGFACT_SEARCH_OPENAI_MODEL",
    "LONGFACT_OPENAI_WEB_SEARCH_MODEL",
    "OPENAI_WEB_SEARCH_MODEL",
) or default_openai_model
openai_search_api_key = openai_search_api_key or openai_api_key
openai_search_base_url = openai_search_base_url or openai_base_url
random_seed = 1
model_options = {
    'gpt_54_mini': f'OPENAI:{default_openai_model}',
    'gpt_4_turbo': 'OPENAI:gpt-4-0125-preview',
    'gpt_4': 'OPENAI:gpt-4-0613',
    'gpt_4_32k': 'OPENAI:gpt-4-32k-0613',
    'gpt_35_turbo': 'OPENAI:gpt-3.5-turbo-0125',
    'gpt_35_turbo_16k': 'OPENAI:gpt-3.5-turbo-16k-0613',
    'claude_3_opus': 'ANTHROPIC:claude-3-opus-20240229',
    'claude_3_sonnet': 'ANTHROPIC:claude-3-sonnet-20240229',
    'claude_3_haiku': 'ANTHROPIC:claude-3-haiku-20240307',
    'claude_21': 'ANTHROPIC:claude-2.1',
    'claude_20': 'ANTHROPIC:claude-2.0',
    'claude_instant': 'ANTHROPIC:claude-instant-1.2',
}
model_string = {
    'gpt_54_mini': default_openai_model.replace('-', '').replace('.', ''),
    'gpt_4_turbo': 'gpt4turbo',
    'gpt_4': 'gpt4',
    'gpt_4_32k': 'gpt432k',
    'gpt_35_turbo': 'gpt35turbo',
    'gpt_35_turbo_16k': 'gpt35turbo16k',
    'claude_3_opus': 'claude3opus',
    'claude_3_sonnet': 'claude3sonnet',
    'claude_21': 'claude21',
    'claude_20': 'claude20',
    'claude_instant': 'claudeinstant',
}
task_options = {}
root_dir = '/'.join(os.path.abspath(__file__).split('/')[:-2])
path_to_data = 'datasets/'
path_to_result = 'results/'
