import asyncio
from llm_parser import parse_question_with_llm

async def main():
    result = await parse_question_with_llm("What is 2 + 2?")
    print("LLM Response:", result)

if __name__ == "__main__":
    asyncio.run(main())
