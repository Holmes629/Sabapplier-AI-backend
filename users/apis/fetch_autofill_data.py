import google.generativeai as genai
import json

# get the html response from the website
def get_autofill_data(html_data, user_data):
    # fetch autofill data from ai api using html data and user data
    api_key = "AIzaSyC_OPZO2FLYsAs-Gtvjx-5AQGYKBDUul5k"
    api_input = f"Website Text: {html_data}\nuser json data: {user_data}"
    instructions ="I have provided website html data and user json, for each and every input field provide class name of the field (if there are many class names only provide first class name and also add dot at the front) as key and value as its relative user data. For non direct or descriptive field generate relevant response using user data and assign the value. Only ouput list of json data with key as input html class name and value as user relevant data, don't give extra response except response list of json."
    
    user_prompt = api_input+ instructions   
    client = genai.configure(api_key=api_key)
    response = genai.GenerativeModel('gemini-2.0-flash').generate_content(user_prompt)

    autofillData = "".join(response.text.split('\n')[1:-1])
    print('1. Fetched auto fill data....')
    return autofillData


