from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
import requests
import time
import bs4 as bs
from selenium import webdriver
app = Flask(__name__)

#chatgpt
import os
import openai

import key
openai.api_key = key.SECRET_KEY

style_data = {
    "use case": "",
    "likes": "",
    "styles": "",
    "brands": "",
    "suggestions": [],
    "brand recs": [],
    "brand imgs": []
}

#set use case
@app.route('/submit_use', methods=['GET', 'POST'])
def submit_use():
    global style_data

    data = request.get_json()

    style_data["use case"] = data["use case"] 
    
    return jsonify(style_data)

#set style and likes
@app.route('/user_info', methods=['GET', 'POST'])
def submit_user_style():
    global style_data

    data = request.get_json()
    
    style_data["likes"] = data["likes"]
    style_data["styles"] = data["styles"]

    return jsonify(style_data)

#style_suggestions
@app.route('/style_suggestions', methods=['GET', 'POST'])
def get_suggestions():
    global style_data

    use = style_data["use case"]
    likes = style_data["likes"]
    styles = style_data["styles"]

    style_sug = get_suggestions_for_expansion(use, likes, styles)
    style_data["suggestions"] = style_sug

    return jsonify(style_data)

def parse_response_from_gpt(gpt_response):
    output = gpt_response.splitlines()
    #response_list = output[:-1]
    #print(output)

    new_responses = []
    for i, response in enumerate(output):
        response = response.strip()
        if response != "":
            new_responses.append(response)
    print(new_responses)
    return new_responses

def get_suggestions_for_expansion(use, likes, styles):
    gpt_prompt = "I want to "+use+". I like wearing "+likes+" and "+styles+" styles. Give me style suggestions like this: \n 1. suggestion \n 2. suggestion \n 3. suggestion."
    print(gpt_prompt)

    response = openai.Completion.create (
        model="text-davinci-003",
        prompt=gpt_prompt, 
        max_tokens=1000,
        temperature=0.4)["choices"][0]["text"]

    #parsing
    suggestion_output = []
    try:
        suggestion_output = parse_response_from_gpt(response)
    except:
        print("ERROR: unable to parse playlist from gpt")
        print(response)
    return suggestion_output

#set user brands
@app.route('/submit_brands', methods=["GET", "POST"])
def submit_brands():
   data = request.get_json()
   
   style_data["brands"] = data["brands"]
   
   return jsonify(style_data)

#gets brand suggestions
@app.route('/brand_suggestions', methods=['GET', 'POST'])
def get_brands_list():
    global style_data

    brands = style_data["brands"]
    imgs = style_data["brand imgs"]

    brands_list = get_brands_expansion(brands)
    #brands_imgs = custom_search(brands_list, 5)
    style_data["brand recs"] = brands_list
    #style_data["brand imgs"] = brands_imgs

    return jsonify(style_data)

def get_brands_expansion(brands):
    gpt_prompt = "I like brands like "+brands+". what are some similar lesser known clothing brands? give 5 suggestions like this: \n 1. suggestion: description \n 2. suggestion: description \n 3. suggestion: description"
    print(gpt_prompt)

    response = openai.ChatCompletion.create (
        model="gpt-3.5-turbo",
        messages = [
            {'role': 'system', 
             'content': 'You are my stylist'},
            {'role': 'user', 'content': gpt_prompt}
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    output = response['choices'][0]['message']['content']

    #parsing
    suggestion_output = []
    try:
        suggestion_output = parse_response_from_gpt(output)
        blist = parse_brand_for_imgs(suggestion_output)
        url = get_brand_images(blist)
    except:
        print("ERROR: unable to parse brands from gpt")
        print(response)

    return suggestion_output

def parse_brand_for_imgs(brands_output):
    new_brands = []
    for brand in brands_output:
        brand_name = brand.split(":")[0]
        stripped = brand_name[3:]
        new_brands.append(stripped)
    print(new_brands)
    return new_brands

def get_brand_images(brands_output):
    queries = []
    url = "https://www.pinterest.co.uk/search/pins/?q="
    for brand in brands_output:
        brand = brand.replace(" ", "%20").lower() + "%20clothing&rs=typed"
        query = url + brand
        queries.append(query)

    driver = webdriver.Chrome()
    
    imgs_brands = []
    for query in queries:
        driver.get(query)
        time.sleep(5)
        src = driver.page_source
        finder = bs.BeautifulSoup(src, features="html.parser")
        img = finder.find_all('img')

        imgs = []
        for link in img:
            src_attr = link.get('src')
            imgs.append(src_attr)
        only = imgs[:5]
        imgs_brands.append(only)
    
    print(imgs_brands)
    return imgs_brands

            
@app.route("/")
def home():
    return render_template('new.html', data=style_data)

if __name__ == '__main__':
    app.run(debug = True, port = 8000)    
    #app.run(debug = True)