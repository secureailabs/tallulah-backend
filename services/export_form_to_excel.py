import uuid
from datetime import datetime

import pandas as pd
from pymongo import MongoClient


# Anonymization function
def anonymize_data(doc):
    # Anonymize the 'values' field
    anon_values = {}

    # Anonymize specific fields
    anon_values["_id"] = str(uuid.uuid4())  # Replace with a new UUID
    anon_values["creation_time"] = doc["creation_time"]

    for key, value in doc["values"].items():
        if key in ["consent", "age", "assistanceImpact", "patientStory"]:
            anon_values[key] = value["value"]

    return anon_values


# Connect to MongoDB
# TODO: Replace the connection string with the correct one
client = MongoClient("TODO")
db = client["tallulah-prod-wanted-lamprey"]
collection = db["form_data"]

# Fetch the data from MongoDB
# TODO: Replace the query with the correct one
documents = collection.find({"form_template_id": "", "state": "ACTIVE", "values.consent.value": ["Yes"]})

# Initialize an empty list to store the anonymized data
anonymized_data = []


# Process each document
for doc in documents:
    anon_doc = anonymize_data(doc)
    anonymized_data.append(anon_doc)

# Convert the anonymized data to a DataFrame
df_list = []
for data in anonymized_data:
    form_data = {}
    form_data["_id"] = data["_id"]
    form_data["creation_time"] = data["creation_time"]
    form_data["age"] = data["age"]
    form_data["consent"] = data["consent"]
    form_data["assistanceImpact"] = data["assistanceImpact"]
    form_data["patientStory"] = data["patientStory"]
    df_list.append(form_data)

df = pd.DataFrame(df_list)

# Save the DataFrame to an Excel file
file_name = f'anonymized_form_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
df.to_excel(file_name, index=False)

print(f"Data has been exported and anonymized to {file_name}")
