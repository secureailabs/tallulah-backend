import asyncio
import json
from datetime import datetime

import aiohttp
import pandas as pd
from numpy import NaN, add

# TODO 1
auth_token = ""
# TODO 2
form_template_id = ""


async def post_form_data(json_data):
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + auth_token,
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://tallulah.ai/api/form-data/manual", headers=headers, data=json_data, ssl=False
        ) as response:
            print(response.status)
            print(response.headers)

# TODO: 3 This function is data dependent and needs to be updated
def transform_data(row):
    # Row has a structure like this:
    # ,Date Submitted,First Name,Last Name,Email,Street address,State/Province,Zip/Postal Code,Country,Age,Date of Birth,Pronouns,Where is/are your tumor(s)?,Briefly summarize your experience of diagnosis.,Briefly describe your past and current treatment.,Desmoid Tumor Story,Photos,One-Minute Video,Don't worry! I uploaded At least one photo of myself or the patient alone (or with a pet) per the guidelines above.,Don't worry! I also uploaded...,Talking to the Media (For U.S. Patients),DTRF Release and Consent,Please add me to The DTRF Newsletter list to receive bimonthly email newsletters.

    # Which needs to be transformed into this sample structure:
    # values = {
    #     "first_name": {"value": "Aman", "label": "First Name", "type": "STRING"},
    #     "last_name": {"value": "Test", "label": "Last Name", "type": "STRING"},
    #     "email": {"value": "dtrf_tesst@sail.com", "label": "Email", "type": "EMAIL"},
    #     "street_address": {"value": "something", "label": "Street Address", "type": "STRING"},
    #     "state_province": {"value": "Utah", "label": "State/Province", "type": "STRING"},
    #     "zip_postal_code": {"value": "20202", "label": "ZIP/Postal Code", "type": "STRING"},
    #     "country": {"value": "USA", "label": "Country", "type": "STRING"},
    #     "age": {"value": {"$numberInt": "23"}, "label": "Age", "type": "NUMBER"},
    #     "date_of_birth": {"value": "2024-08-07", "label": "Date of Birth", "type": "DATE"},
    #     "pronouns": {"value": "she/her", "label": "Pronouns", "type": "SELECT"},
    #     "tumor_location": {"value": "sdsd", "label": "Where is/are your tumor(s)?", "type": "STRING"},
    #     "diagnosis_experience": {
    #         "value": "experience of diagnosis.",
    #         "label": "Experience of Diagnosis",
    #         "type": "TEXTAREA",
    #     },
    #     "treatment_description": {
    #         "value": "current treatment.",
    #         "label": "Past and Current Treatment",
    #         "type": "TEXTAREA",
    #     },
    #     "desmoid_story": {
    #         "value": " questions and share your story.",
    #         "label": "Desmoid Tumor Story",
    #         "type": "TEXTAREA",
    #     },
    #     "photos": {"value": [], "label": "photos", "type": "FILE"},
    #     "video": {"value": [], "label": "video", "type": "FILE"},
    #     "uploaded atleast one photo": {
    #         "value": [
    #             "Don't worry! I uploaded At least one photo of myself or the patient alone (or with a pet) per the guidelines above."
    #         ],
    #         "label": "Don't worry! I uploaded At least one photo of myself or the patient alone (or with a pet) per the guidelines above.",
    #         "type": "CHECKBOX",
    #     },
    #     "i have uploaded": {
    #         "value": ["A one-minute video per the guidelines above"],
    #         "label": "Don't worry! I also uploaded... ",
    #         "type": "RADIO",
    #     },
    #     "media_consent": {"value": ["Yes"], "label": "Talking to the Media (For U.S. Patients)", "type": "RADIO"},
    #     "DTRF Release and Consent": {
    #         "value": [
    #             "PATIENT 18 OR OLDER: I, the person in this story/photo/video, consent and grant to DTRF the right and permission to use and publish statements made by me and my image in any and all media formats for the purposes authorized here: staff/volunteer/board member education and internal foundation meetings; DTRF website and social media channels; discussions with advocacy partners; pharmaceutical companies and the FDA; presentations or brochures; media and press releases, and other similar purposes to publicize or present DTRF’s programs in other forums. I understand that my participation is voluntary and I release and discharge DTRF from any and all liability arising out of or connected to their exercise of these publicity rights for the authorized purpose(s) described above. There is no time limit on the validity of this release nor is there any geographic limitation as to where these publicity rights may be exercised."
    #         ],
    #         "label": "DTRF Release and Consent",
    #         "type": "RADIO",
    #     },
    #     "Please add me to The DTRF Newsletter list to receive bimonthly email newsletters.": {
    #         "value": ["Please add me to The DTRF Newsletter list to receive bimonthly email newsletters."],
    #         "label": "Please add me to The DTRF Newsletter list to receive bimonthly email newsletters.",
    #         "type": "CHECKBOX",
    #     },
    #     "profilePicture": {"value": [], "label": "profilePicture", "type": "IMAGE"},
    #     "tags": {
    #         "value": "Treatment History, USA, Desmoid Tumor Story, Female, Utah, Diagnosis Experience, Tumor Location",
    #         "label": "Tags",
    #         "type": "STRING",
    #     },
    # }
    if row["Don't worry! I uploaded At least one photo of myself or the patient alone (or with a pet) per the guidelines above."] == "Checked":
        upload_atleast_one_photo = "Yes"
    else:
        upload_atleast_one_photo = "No"

    if row["Please add me to The DTRF Newsletter list to receive bimonthly email newsletters."] == "Checked":
        add_to_newsletter = "Yes"
    else:
        add_to_newsletter = "No"

    values = {
        "firstName": {"value": f"{row["First Name"]}", "label": "First Name", "type": "STRING"},
        "lastName": {"value": f"{row["Last Name"]}", "label": "Last Name", "type": "STRING"},
        "email": {"value": f"{row["Email"]}", "label": "Email", "type": "EMAIL"},
        "street_address": {"value": f"{row["Street address"]}", "label": "Street Address", "type": "STRING"},
        "state_province": {"value": f"{row["State/Province"]}", "label": "State/Province", "type": "STRING"},
        "zip_postal_code": {"value": f"{row["Zip/Postal Code"]}", "label": "ZIP/Postal Code", "type": "STRING"},
        "country": {"value": f"{row["Country"]}", "label": "Country", "type": "STRING"},
        "age": {"value": f"{row["Age"]}", "label": "Age", "type": "NUMBER"},
        "date_of_birth": {"value": f"{row["Date of Birth"]}", "label": "Date of Birth", "type": "DATE"},
        "pronouns": {"value": f"{row["Pronouns"]}", "label": "Pronouns", "type": "SELECT"},
        "tumor_location": {"value": f"{row["Where is/are your tumor(s)?"]}", "label": "Where is/are your tumor(s)?", "type": "TEXTAREA"},
        "diagnosis_experience": {"value": f"{row["Briefly summarize your experience of diagnosis."]}", "label": "Experience of Diagnosis", "type": "TEXTAREA"},
        "treatment_description": {"value": f"{row["Briefly describe your past and current treatment."]}", "label": "Past and Current Treatment", "type": "TEXTAREA"},
        "desmoid_story": {"value": f"{row["Desmoid Tumor Story"]}", "label": "Desmoid Tumor Story", "type": "TEXTAREA"},
        "photos": {"value": [], "label": "photos", "type": "IMAGE"},
        "video": {"value": [], "label": "video", "type": "VIDEO"},
        "uploaded atleast one photo": {"value": f"{upload_atleast_one_photo}", "label": "Don't worry! I uploaded At least one photo of myself or the patient alone (or with a pet) per the guidelines above.", "type": "RADIO"},
        "i have uploaded": {"value": f"{row["Don't worry! I also uploaded..."]}", "label": "Don't worry! I also uploaded... ", "type": "RADIO"},
        "media_consent": {"value": f"{row["Talking to the Media (For U.S. Patients)"]}", "label": "Talking to the Media (For U.S. Patients)", "type": "RADIO"},
        "DTRF Release and Consent": {"value": f"{row["DTRF Release and Consent"]}", "label": "DTRF Release and Consent", "type": "RADIO"},
        "Please add me to The DTRF Newsletter list to receive bimonthly email newsletters.": {"value": f"{add_to_newsletter}", "label": "Please add me to The DTRF Newsletter list to receive bimonthly email newsletters.", "type": "RADIO"},
        "profilePicture": {"value": [], "label": "profilePicture", "type": "IMAGE"},
    }

    # Date format is 01/19/2024
    date_added = datetime.strptime(row["Date Submitted"], "%m/%d/%Y").isoformat()

    return values, date_added


async def main(df):
    tasks = []

    for index, row in df.iterrows():
        values, date_added = transform_data(row)
        print(values, date_added)

        body = {
            "form_template_id": form_template_id,
            "values": values,
            "state": "ACTIVE",
            "creation_time": date_added,
        }

        tasks.append(post_form_data(json.dumps(body)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":

    df1 = pd.read_csv("2024-Submit_Your_Story.csv")
    print(df1)
    asyncio.run(main(df1))
