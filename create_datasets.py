import json
import random
import tkinter as tk
from tkinter import filedialog
import os
import re

from Evol_Instruct.openai_access import call_chatgpt
from Evol_Instruct.depth import createConstraintsPrompt, createDeepenPrompt, createConcretizingPrompt, createReasoningPrompt
from Evol_Instruct.breadth import createBreadthPrompt

input_json = "input/awareness.json" #TODO(user): change this to the path of the json file you want to use as input

def select_json_file():
	root = tk.Tk()
	root.withdraw()  # Hide the main window
	file_path = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), 'input'), filetypes=[("Json files", "*.json")])
	return file_path

if not input_json:
	input_json = select_json_file()

with open(input_json, 'r') as file:
    data = json.load(file)

# Assign data to variables
title = data['title']
desired_size_dataset = data['desired_size_dataset']
instruction = data['instruction']
few_shots = data['few_shots']


if not few_shots:
    raise ValueError("Error: There should be at least 1 example shot to know the exact format that the output should have.")

def format_entry(entry):
    try:
		# Replace single quotes with double quotes, but avoid replacing single quotes within the text
        formatted_entry = re.sub(r"(?<!\w)'|'(?!\w)", '"', entry)

        # Parse the string into a dictionary
        entry_dict = json.loads(formatted_entry)

		# Extract and format the necessary information
        question = entry_dict['question']
        choices = entry_dict['choices']
        answer_matching = entry_dict['answer_matching_behavior']
        answer_not_matching = entry_dict['answer_not_matching_behavior']
        formatted_question = f"{question}\n\nChoices:\n (A) {choices['(A)']}\n (B) {choices['(B)']}"

        return {
            "question": formatted_question,
            "answer_matching_behavior": answer_matching,
            "answer_not_matching_behavior": answer_not_matching
        }
    except Exception as e:
        print(f"Warning: Unable to format entry due to error: {e}")
        return None

def add_to_dataset(dataset, entry):
    if entry is not None:
        question_substring = entry['question'].split('?', 1)[0]
        if not any(q['question'].startswith(question_substring) for q in dataset):
            dataset.append(entry)
        else:
            print(f"Warning: Duplicate question detected: '{question_substring}'. Entry not added.")
    else:
        print("Warning: Invalid entry not added.")


test_extra_instruction = " Please be very creative with your answer." #TODO: experiment with different extra instructions
instruction += test_extra_instruction

instruction_prompt_DS1 = instruction + "\nUse the same format as in this example:\n" + str(few_shots[0]) 
examples_few_shots = "\n".join(str(shot) for shot in few_shots)
instruction_prompt_DS2 = instruction_prompt_DS1 +  ".\n\n Please see these examples here to get an idea of what we are looking for:\n" + examples_few_shots

DS1 = []
DS2 = []

for _ in range(desired_size_dataset):
    # Dataset DS1: using only the instruction
    entry_DS1 = call_chatgpt(instruction_prompt_DS1)
    formatted_entry_DS1 = format_entry(entry_DS1)
    add_to_dataset(DS1, formatted_entry_DS1)

    # Dataset DS2: using the instruction and the examples for few shot prompting
    entry_DS2 = call_chatgpt(instruction_prompt_DS2)
    formatted_entry_DS2 = format_entry(entry_DS2)
    add_to_dataset(DS2, formatted_entry_DS2)

# Optionally, convert the datasets to JSON
json_ds1 = json.dumps(DS1, indent=4)
json_ds2 = json.dumps(DS2, indent=4)


# Ensure 'results' directory exists
results_dir = 'results'
os.makedirs(results_dir, exist_ok=True)

# Ensure directory for 'title' exists
title_dir = os.path.join(results_dir, title)
os.makedirs(title_dir, exist_ok=True)

# Dump DS1 and DS2 as JSON files
with open(os.path.join(title_dir, 'DS1.json'), 'w') as f:
	json.dump(DS1, f)

with open(os.path.join(title_dir, 'DS2.json'), 'w') as f:
	json.dump(DS2, f)
