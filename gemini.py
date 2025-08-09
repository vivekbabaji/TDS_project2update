from google import genai
import pandas as pd

client = genai.Client(api_key="AIzaSyC3dswe0cmF3HSO8Ay8xkOnyoHwk1OToW4")

df = pd.read_csv("data.csv")
data = df.head(50)

def ans_with_gemini(questions):
    question = f"""
    Quwstion: {questions},
    data: {data}

    Answer the question based on data provided.
    Give only the output answer in json format.

    """



    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=question
    )
    return (response.text)