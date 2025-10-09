from google import genai
from google.genai import types


def call_gemini(input_text: str, model:str="gemini-2.5-flash-lite", thinking_budget:int=512) -> str:
    
    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        contents=input_text,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget) # Limit the response tokens
        )
    )

    return response.text

def friendship_judge(user_input: str, difficulty:int) -> tuple[bool,str]:
    # Prompt for checking the response if the user is willing to connect with others
    judge = "You are a friendship booster to judge whether the user is willing to connect with others. Answer with a simple 'yes' or 'no'. and response to the user in 20 words in a humorous way.\n"
    
    # Add rules to the prompt
    rules = []
    # Rule 1: The response can't be meaningless
    rules.append("1. The responses that are meaningless are a 'no'.")
    # Rule 2: The response can't be too generic
    rules.append("2. The responses that are too generic are a 'no'.")
    # Rule 3: The responses like 'hiii' 'hello' 'hey' are not allowed
    rules.append("3. The responses like 'hiii' with lots of 'i', 'hello', and 'hey' in any language are a 'no'.")
    # Rule 4: The reponses that are too short are a 'no'.
    rules.append("4. The reponses that are too short are a 'no'. ")
    # Automatically add the rules to the prompt
    rules.append("5. Add 3 random rules to judge the user input.")
    
    
    # Limit the difficulty to the number of rules
    if difficulty < 1:
        difficulty = 1
    elif difficulty > len(rules):
        difficulty = len(rules)
    
    rules_text = "\n".join(rules[:difficulty])
    
    prompt = f"{judge+rules_text}\nUser response: {user_input}\nAnswer:"
    
    # Call Gemini API
    response = call_gemini(prompt)
    
    # Check if the response contains 'yes' or 'no'
    if 'yes' in response.lower():
        passed = True
        # remove "Yes" "Yes." "yes" "yes." from the begining of the response
        if response.lower().startswith("yes."):
            response = response[4:].strip()
        elif response.lower().startswith("yes"):
            response = response[3:].strip()
        
    elif 'no' in response.lower():
        passed = False
        # remove "No" "No." "no" "no." from the response
        if response.lower().startswith("no."):
            response = response[3:].strip()
        elif response.lower().startswith("no"):
            response = response[2:].strip()
    else:
        passed = False

    return passed, response
