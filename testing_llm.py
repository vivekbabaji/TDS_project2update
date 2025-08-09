import asyncio
import json
import httpx

from llm_parser import answer_with_data


async def main():
    question = "1. How many $2 bn movies were released before 2000?"
    answer = await answer_with_data(question)
    print("LLM Answer:", answer)

asyncio.run(main())
