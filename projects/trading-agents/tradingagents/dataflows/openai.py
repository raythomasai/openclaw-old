import os
from openai import OpenAI
from anthropic import Anthropic
from .config import get_config


def get_stock_news_openai(query, start_date, end_date):
    config = get_config()
    
    # Handle MiniMax separately (uses Anthropic API)
    if config.get("llm_provider", "").lower() == "minimax":
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        client = Anthropic(base_url=config.get("backend_url"), api_key=api_key)
        
        # MiniMax may not support web_search_preview - return placeholder
        # In production, you'd want to implement alternative search
        return f"[MiniMax] Web search for {query} from {start_date} to {end_date} - feature pending implementation"
    
    # Standard OpenAI path
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Social Media for {query} from {start_date} to {end_date}? Make sure you only get the data posted during that period.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_openai(curr_date, look_back_days=7, limit=5):
    config = get_config()
    
    # Handle MiniMax separately (uses Anthropic API)
    if config.get("llm_provider", "").lower() == "minimax":
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        client = Anthropic(base_url=config.get("backend_url"), api_key=api_key)
        
        return f"[MiniMax] Web search for global news from {look_back_days} days before {curr_date} - feature pending implementation"
    
    # Standard OpenAI path
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search global or macroeconomics news from {look_back_days} days before {curr_date} to {curr_date} that would be informative for trading purposes? Make sure you only get the data posted during that period. Limit the results to {limit} articles.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    
    # Handle MiniMax separately (uses Anthropic API)
    if config.get("llm_provider", "").lower() == "minimax":
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        client = Anthropic(base_url=config.get("backend_url"), api_key=api_key)
        
        return f"[MiniMax] Web search for fundamentals on {ticker} - feature pending implementation"
    
    # Standard OpenAI path
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text
