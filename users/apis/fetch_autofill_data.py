import os
import json
import google.generativeai as genai
from django.conf import settings
from bs4 import BeautifulSoup


def extract_form_only(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    forms = soup.find_all('form')
    return '\n'.join(str(form) for form in forms)


def get_autofill_data(raw_html, user_data):
    try:

        api_key = "AIzaSyC_OPZO2FLYsAs-Gtvjx-5AQGYKBDUul5k"
        form_data = extract_form_only(raw_html)
        
        print("\nform length:", len(form_data))
        MAX_HTML_CHARS = 32000 
        if len(form_data) > MAX_HTML_CHARS:
            form_data = form_data[:MAX_HTML_CHARS]
        
        # If no API key is available, return mock autofill data for testing
        if not api_key:
            print("No Gemini API key found, returning mock autofill data")
            soup = BeautifulSoup(raw_html, 'html.parser')
            mock_data = []
            
            # Find input fields and provide mock data based on user data
            inputs = soup.find_all(['input', 'select', 'textarea'])
            for input_field in inputs:
                field_name = input_field.get('name')
                field_type = input_field.get('type', 'text')
                
                if field_name:
                    selector = f'input[name="{field_name}"]'
                    
                    # Map common field names to user data
                    if field_name in ['email', 'emailAddress', 'user_email']:
                        mock_data.append({selector: user_data.get('email', ''), 'type': 'input'})
                    elif field_name in ['fullName', 'name', 'full_name', 'userName']:
                        mock_data.append({selector: user_data.get('fullName', ''), 'type': 'input'})
                    elif field_name in ['phone', 'phoneNumber', 'phone_number', 'mobile']:
                        mock_data.append({selector: user_data.get('phone_number', ''), 'type': 'input'})
                    elif field_name in ['address', 'permanentAddress']:
                        mock_data.append({selector: user_data.get('permanentAddress', ''), 'type': 'input'})
                    
            return json.dumps(mock_data)


        # Stage 1: Prompt to generate autofill data
        instructions = (
            "### TASK:\n"
            "You are given raw HTML and user JSON. For each and every input field:\n"
            "I want to fill the html form, so help me to fill it using extension script feature, so for that give me output accordingly such that I can fill that data.\n"
            "1. Identify the matching form field using input[name=''], or '.class_name', or '#id' (prefer name).\n"
            "2. For input fields and textareas, fill with relevant user data or similar to it.\n"
            "3. For select fields, choose the most relevant option based on user data, just give the value of the option don't generate anything else, don't choose first option, because its the default option.\n"
            "4. For radio buttons, select the most relevant option based on user data\n"
            "5. For checkboxes, check the most relevant options based on user data, else check the last option.\n"
            "6. For file inputs, provide 'file url from the user data' as a filled value. Also give required file name, size of the file that needs to be uploaded in kb (give the lowest possible size that i can upload), pixel values that document need to have (only give in pixel units if they are in different units convert them to pixels). if you can't find document dimensions in the website use this: photograph-jpg-200x230px-20kb; signature-jpg-140x60px-10kb; Left thumb impression-jpg-240x240px-20kb; Hand-written declaration Image-jpg-800x400px-50kb\n"
            "### SPECIAL INSTRUCTIONS FOR FIELD TYPES:\n"
            "- For radio buttons: match the id or name, for the applicable option and select the value closest to user data. If a match isn’t obvious, choose a logically relevant value. give value as checked or unchecked for applicable radio button\n"
            "- For <select> dropdowns: match the name or id, and select the value closest to user data. If a match isn’t obvious, choose a logically relevant value.\n"
            "- For file inputs: if user JSON contains file URL or document name, assign it. Else, use 'NA'.\n"
            "- For checkboxes: assign 'checked' if the value applies to user, otherwise 'unchecked'.\n"
            "- Always include 'type': 'select', 'file', 'checkbox', 'radio', or 'input' as appropriate.\n"
            "[\n"
            "  {'input[name=\"username\"]': 'JohnDoe', 'type': 'input'},\n"
            "  {'input[name=\"email\"]': 'john@email.com', 'type': 'input'},\n"
            "  {'#id': 'checked', 'type': 'radio'},\n"
            "  {'input[name=\"file\"]': 'file_url', 'type': 'file', 'file_name': 'file_name.ext', 'file_type': 'jpe', 'size':'5kb', 'pixels': '500x600px'}"
            "]\n"
            "### RESPONSE:\n"
        )

        # Combine input
        prompt_stage_1 = f"Website Text: {form_data}\nUser JSON: {user_data}\n\n{instructions}"

        # Stage 1: Use Gemini Flash to generate raw autofill data
        genai.configure(api_key=api_key)
        model_flash = genai.GenerativeModel('gemini-2.0-flash')
        response_stage_1 = model_flash.generate_content(
            prompt_stage_1,  
        )
        raw_autofill = "".join(response_stage_1.text.split('\n')[1:-1])

        print("🔹 Stage 1 autofill data (raw):", raw_autofill)
        # return raw_autofill

        # Stage 2: Prompt to review and correct autofill data
        review_prompt = (
            "### TASK:\n"
            "You are given HTML form content and user data, along with autofill JSONs generated by another AI model.\n"
            "Your job is to **review** and **improve the accuracy** of the autofill data by:\n"
            "- Validating matches between field names and user data\n"
            "1. For input fields and textareas, fill with relevant user data or similar to it.\n"
            "2. For select fields, choose the most relevant option based on user data, just give the value of the option don't generate anything else, if none choose last option.\n"
            "3. For radio buttons, select the most relevant option based on user data\n"
            "4. For checkboxes, check the most relevant options based on user data, else check the last option.\n"
            "5. For file inputs, provide 'file url from the user data' as a filled value. Also give required file name, size of the file that needs to be uploaded in kb (give the lowest possible size that i can upload), pixel values that document need to have (only give in pixel units if they are in different units convert them to pixels).if you can't find document dimensions in the website use this: photograph-jpg-200x230px-20kb; signature-jpg-140x60px-10kb; Left thumb impression-jpg-240x240px-20kb; Hand-written declaration Image-jpg-800x400px-50kb\n\n"
            "- For radio buttons: match the id or name, for the applicable option and select the value closest to user data. If a match isn’t obvious, choose a logically relevant value. give value as checked or unchecked for applicable radio button\n"
            "- Correcting field values if needed\n"
            "- Ensuring logical matches for select/dropdowns, checkboxes, and files\n"
            "- Fixing inconsistent or obviously wrong values\n\n"
            f"Website HTML:\n{form_data}\n\n"
            f"User JSON:\n{user_data}\n\n"
            f"AI-generated autofill JSON:\n{raw_autofill}\n\n"
            "[\n"
            "  {'input[name=\"username\"]': 'JohnDoe', 'type': 'input'},\n"
            "  {'input[name=\"email\"]': 'john@email.com', 'type': 'input'}\n"
            "  {'#id': 'checked', 'type': 'radio'},\n"
            "  {'input[name=\"file\"]': 'file_url', 'type': 'file', 'file_name': 'file_name.ext', 'file_type': 'jpe', 'size':'5kb', 'pixels': '500x600px'}"
            "]\n"
            "dont generate anything, any explanations or anything except json response\n"
        )

        # Stage 2: Use Gemini 1.5 Pro to review and refine
        model_refiner = genai.GenerativeModel('gemini-2.0-flash')  # More accurate model
        response_stage_2 = model_refiner.generate_content(review_prompt)
        improved_autofill = "".join(response_stage_2.text.split('\n')[1:-1])

        print("✅ Stage 2 improved autofill data:", improved_autofill)

        return improved_autofill 
    except Exception as e:
        print(f"Error generating autofill data: {e}")
        return json.dumps([])