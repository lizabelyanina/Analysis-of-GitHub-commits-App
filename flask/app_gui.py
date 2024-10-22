import app_gui as tk
import requests
import json

def submit_input():
    user_input = entry.get()
    response = requests.post('http://127.0.0.1:5000/submit', json={'user_input': user_input})
    response_data = response.json()
    result_label.config(text=response_data['response'])

# Create the main window
root = tk.Tk()
root.title("Flask Input Example")

# Create and place the input field
entry_label = tk.Label(root, text="Enter something:")
entry_label.pack()

entry = tk.Entry(root)
entry.pack()

# Create and place the submit button
submit_button = tk.Button(root, text="Submit", command=submit_input)
submit_button.pack()

# Create and place the result label
result_label = tk.Label(root, text="")
result_label.pack()

# Run the Tkinter event loop
root.mainloop()