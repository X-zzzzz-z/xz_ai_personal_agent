from dotenv import load_dotenv
import os

from openai import OpenAI


load_dotenv()


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def chat(messages, tools=None):

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        tools=tools
    )

    answer = response.choices[0].message

    return answer