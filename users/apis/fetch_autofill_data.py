import google.generativeai as genai
from django.conf import settings
    

def get_autofill_data(html_data, user_data):
    # fetch autofill data from ai api using html data and user data
    api_key = "AIzaSyC_OPZO2FLYsAs-Gtvjx-5AQGYKBDUul5k"
    api_input = f"Website Text: {html_data}\nuser json data: {user_data}"
    instructions ="I have provided website html data and user json, for each and every input field provide input name (in the format 'input[name='input_name']') or class name (it should be in the format '.class_name') or class id (it should be in the format '#class_id') of the field (if there are many class names only provide first class name ) as key and value as its relative user data, also specify input type as file or input or textarea or label or checkbox, ex: [  {'input[name='username']': 'demo', 'type': 'input'},  {'input[name='email']': 'demoemail@gmail.com', 'type': 'file' }]. If values are empty don't fill them as null, fill them as NA. For non direct or descriptive field generate relevant response using user data and assign the value. Also follow order while giving the json, the order should be same as the elements from top to bottom. Only output list of json data with key as input html class name and value as user relevant data, don't give extra response except response list of json."
    
    user_prompt = api_input+ instructions   
    client = genai.configure(api_key=api_key)
    response = genai.GenerativeModel('gemini-2.0-flash').generate_content(user_prompt)

    autofillData = "".join(response.text.split('\n')[1:-1])
    print('1. Fetched auto fill data....')
    return autofillData


