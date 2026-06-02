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
"""Rates a single atomic fact for accuracy."""

import dataclasses
import re
from typing import Any

import requests

# pylint: disable=g-bad-import-order
from common import modeling
from common import shared_config
from common import utils
from eval.safe import config as safe_config
from eval.safe import query_serper
# pylint: enable=g-bad-import-order

SUPPORTED_LABEL = 'Supported'
NOT_SUPPORTED_LABEL = 'Not Supported'

_STATEMENT_PLACEHOLDER = '[STATEMENT]'
_KNOWLEDGE_PLACEHOLDER = '[KNOWLEDGE]'
_NEXT_SEARCH_FORMAT = f"""\
Instructions:
1. You have been given a STATEMENT and some KNOWLEDGE points.
2. Your goal is to try to find evidence that either supports or does not \
support the factual accuracy of the given STATEMENT.
3. To do this, you are allowed to issue ONE Google Search query that you think \
will allow you to find additional useful evidence.
4. Your query should aim to obtain new information that does not appear in the \
KNOWLEDGE. This new information should be useful for determining the factual \
accuracy of the given STATEMENT.
5. Format your final query by putting it in a markdown code block.

KNOWLEDGE:
{_KNOWLEDGE_PLACEHOLDER}

STATEMENT:
{_STATEMENT_PLACEHOLDER}
"""
_FINAL_ANSWER_FORMAT = f"""\
Instructions:
1. You have been given a STATEMENT and some KNOWLEDGE points.
2. Determine whether the given STATEMENT is supported by the given KNOWLEDGE. \
The STATEMENT does not need to be explicitly supported by the KNOWLEDGE, but \
should be strongly implied by the KNOWLEDGE.
3. Before showing your answer, think step-by-step and show your specific \
reasoning. As part of your reasoning, summarize the main points of the \
KNOWLEDGE.
4. If the STATEMENT is supported by the KNOWLEDGE, be sure to show the \
supporting evidence.
5. After stating your reasoning, restate the STATEMENT and then determine your \
final answer based on your reasoning and the STATEMENT.
6. Your final answer should be either "{SUPPORTED_LABEL}" or \
"{NOT_SUPPORTED_LABEL}". Wrap your final answer in square brackets.

KNOWLEDGE:
{_KNOWLEDGE_PLACEHOLDER}

STATEMENT:
{_STATEMENT_PLACEHOLDER}
"""


@dataclasses.dataclass()
class GoogleSearchResult:
  query: str
  result: str


@dataclasses.dataclass()
class FinalAnswer:
  response: str
  answer: str


def call_search(
    search_query: str,
    search_type: str = safe_config.search_type,
    num_searches: int = safe_config.num_searches,
    serper_api_key: str = shared_config.serper_api_key,
    brave_search_api_key: str = shared_config.brave_search_api_key,
    openai_api_key: str = shared_config.openai_search_api_key,
    openai_base_url: str = shared_config.openai_search_base_url,
    openai_web_search_model: str = shared_config.openai_web_search_model,
    search_postamble: str = '',  # ex: 'site:https://en.wikipedia.org'
) -> str:
  """Call Google Search to get the search result."""
  search_query += f' {search_postamble}' if search_postamble else ''

  if search_type == 'serper':
    serper_searcher = query_serper.SerperAPI(serper_api_key, k=num_searches)
    return serper_searcher.run(search_query, k=num_searches)
  elif search_type == 'brave':
    return _call_brave_search(search_query, brave_search_api_key, num_searches)
  elif search_type == 'openai_web':
    return _call_openai_web_search(
        search_query=search_query,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        model_name=openai_web_search_model,
        num_searches=num_searches,
    )
  else:
    raise ValueError(f'Unsupported search type: {search_type}')


def _call_brave_search(
    search_query: str,
    brave_search_api_key: str,
    num_searches: int,
) -> str:
  """Call Brave Search and format web results as SAFE evidence."""
  assert brave_search_api_key, 'Missing brave_search_api_key.'
  response = requests.get(
      'https://api.search.brave.com/res/v1/web/search',
      headers={
          'X-Subscription-Token': brave_search_api_key,
          'Accept': 'application/json',
      },
      params={'q': search_query, 'count': num_searches},
      timeout=30,
  )
  response.raise_for_status()
  data = response.json()
  results = data.get('web', {}).get('results', [])[:num_searches]
  snippets = []
  for result in results:
    title = result.get('title', '')
    url = result.get('url', '')
    description = result.get('description', '')
    extra_snippets = result.get('extra_snippets') or []
    lines = []
    if title:
      lines.append(f'Title: {title}')
    if url:
      lines.append(f'URL: {url}')
    if description:
      lines.append(f'Snippet: {description}')
    for extra in extra_snippets:
      if extra:
        lines.append(f'Snippet: {extra}')
    if lines:
      snippets.append('\n'.join(lines))
  return '\n\n'.join(snippets) if snippets else query_serper.NO_RESULT_MSG


def _call_openai_web_search(
    search_query: str,
    openai_api_key: str,
    openai_base_url: str,
    model_name: str,
    num_searches: int,
) -> str:
  """Call OpenAI Responses web_search and format cited output as evidence."""
  assert openai_api_key, 'Missing openai_api_key.'
  base_url = openai_base_url or 'https://api.openai.com/v1'
  endpoint = f'{base_url.rstrip("/")}/responses'
  response = requests.post(
      endpoint,
      headers={
          'Authorization': f'Bearer {openai_api_key}',
          'Content-Type': 'application/json',
      },
      json={
          'model': model_name,
          'tools': [{'type': 'web_search'}],
          'input': (
              'Search the web for evidence relevant to this fact-checking '
              f'query. Return concise evidence with sources: {search_query}'
          ),
      },
      timeout=120,
  )
  response.raise_for_status()
  text, citations = _extract_openai_web_evidence(response.json())
  evidence = []
  if text:
    evidence.append(f'Web search summary: {text}')
  for citation in citations[:num_searches]:
    title = citation.get('title') or ''
    url = citation.get('url') or ''
    lines = []
    if title:
      lines.append(f'Title: {title}')
    if url:
      lines.append(f'URL: {url}')
    if lines:
      evidence.append('\n'.join(lines))
  return '\n\n'.join(evidence) if evidence else query_serper.NO_RESULT_MSG


def _extract_openai_web_evidence(
    response_data: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
  """Extract text and URL citations from Responses API output."""
  texts = []
  citations = []
  if response_data.get('output_text'):
    texts.append(str(response_data['output_text']))

  for item in response_data.get('output', []):
    for content in item.get('content', []):
      text = content.get('text')
      if text:
        texts.append(text)
      for annotation in content.get('annotations', []):
        citation = annotation.get('url_citation') or {}
        url = citation.get('url')
        if url:
          citations.append({
              'title': citation.get('title', ''),
              'url': url,
          })
  return '\n'.join(texts), citations


def maybe_get_next_search(
    atomic_fact: str,
    past_searches: list[GoogleSearchResult],
    model: modeling.Model,
    debug: bool = safe_config.debug_safe,
) -> GoogleSearchResult | None:
  """Get the next query from the model."""
  knowledge = '\n'.join([s.result for s in past_searches])
  knowledge = 'N/A' if not knowledge else knowledge
  full_prompt = _NEXT_SEARCH_FORMAT.replace(_STATEMENT_PLACEHOLDER, atomic_fact)
  full_prompt = full_prompt.replace(_KNOWLEDGE_PLACEHOLDER, knowledge)
  full_prompt = utils.strip_string(full_prompt)
  model_response = model.generate(full_prompt, do_debug=debug)
  query = utils.extract_first_code_block(model_response, ignore_language=True)

  if model_response and query:
    return GoogleSearchResult(query=query, result=call_search(query))

  return None


def maybe_get_final_answer(
    atomic_fact: str,
    searches: list[GoogleSearchResult],
    model: modeling.Model,
    debug: bool = safe_config.debug_safe,
) -> FinalAnswer | None:
  """Get the final answer from the model."""
  knowledge = '\n'.join([search.result for search in searches])
  full_prompt = _FINAL_ANSWER_FORMAT.replace(
      _STATEMENT_PLACEHOLDER, atomic_fact
  )
  full_prompt = full_prompt.replace(_KNOWLEDGE_PLACEHOLDER, knowledge)
  full_prompt = utils.strip_string(full_prompt)
  model_response = model.generate(full_prompt, do_debug=debug)
  answer = utils.extract_first_square_brackets(model_response)
  answer = re.sub(r'[^\w\s]', '', answer).strip()

  if model_response and answer in [SUPPORTED_LABEL, NOT_SUPPORTED_LABEL]:
    return FinalAnswer(response=model_response, answer=answer)

  return None


def check_atomic_fact(
    atomic_fact: str,
    rater: modeling.Model,
    max_steps: int = safe_config.max_steps,
    max_retries: int = safe_config.max_retries,
    debug: bool = safe_config.debug_safe,
) -> tuple[FinalAnswer | None, dict[str, Any]]:
  """Check if the given atomic fact is supported."""
  search_results = []

  for _ in range(max_steps):
    next_search, num_tries = None, 0

    while not next_search and num_tries <= max_retries:
      next_search = maybe_get_next_search(atomic_fact, search_results, rater)
      num_tries += 1

    if next_search is None:
      utils.maybe_print_error('Unsuccessful parsing for `next_search`')
      break
    else:
      search_results.append(next_search)

  search_dicts = {
      'google_searches': [dataclasses.asdict(s) for s in search_results]
  }
  final_answer, num_tries = None, 0

  while not final_answer and num_tries <= max_retries:
    num_tries += 1
    final_answer = maybe_get_final_answer(
        atomic_fact, searches=search_results, model=rater, debug=debug
    )

  if final_answer is None:
    utils.maybe_print_error('Unsuccessful parsing for `final_answer`')

  return final_answer, search_dicts
