import asyncio
import random
import time
import uuid
from collections import defaultdict

import aiohttp
from faker import Faker

trials = 10000


def generate_fake_patient_data(repository_id):
    fake = Faker()

    patient_id = str(uuid.uuid4())
    name = fake.name()
    primary_cancer_diagnosis = fake.word()
    social_worker_name = fake.name()
    social_worker_organization = fake.company()
    date_of_diagnosis = fake.date()
    age = random.randint(18, 90)

    guardians = []
    for _ in range(random.randint(1, 3)):
        guardian = {
            "relationship": fake.word(),
            "name": fake.name(),
            "employer": fake.company(),
            "email": fake.email(),
            "phone": fake.phone_number(),
        }
        guardians.append(guardian)

    household_details = fake.text()
    family_net_monthly_income = random.randint(1000, 10000)
    address = fake.address()

    recent_requests = []
    for _ in range(random.randint(1, 5)):
        request = {"id": str(uuid.uuid4()), "purpose": fake.text()}
        recent_requests.append(request)

    data = {
        "patient_id": patient_id,
        "repository_id": repository_id,
        "name": name,
        "primary_cancer_diagnosis": primary_cancer_diagnosis,
        "social_worker_name": social_worker_name,
        "social_worker_organization": social_worker_organization,
        "date_of_diagnosis": date_of_diagnosis,
        "age": age,
        "guardians": guardians,
        "household_details": household_details,
        "family_net_monthly_income": family_net_monthly_income,
        "address": address,
        "recent_requests": recent_requests,
    }

    return data


async def send_request(session, req_id):
    url = "https://test.tallulah.ai/api/patient-profiles/"
    header = {
        "Content-Type": "application/json",
        # TODO: Fill this up before running
        "Authorization": "Bearer ",
        "accept": "application/json",
    }
    # Generate fake data
    patient_data = generate_fake_patient_data("53f0f5ad-0d56-41f5-8905-f043e8af1651")

    async with session.post(url, headers=header, json=patient_data) as response:
        resp = await response.json()
        if response.status != 200:
            print(f"Error: {resp}")
        # print(resp)

    time_taken[req_id].append(time.time())


time_taken = defaultdict(list)


async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(trials):
            time_taken[i].append(time.time())
            task = asyncio.create_task(send_request(session, i))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

    worst_time = 0
    # write time taken to file as csv
    with open("time_taken.csv", "w") as f:
        for i in range(trials):
            f.write(f"{i},{time_taken[i][1] - time_taken[i][0]}\n")
            worst_time = max(worst_time, time_taken[i][1] - time_taken[i][0])

    print(f"Worst time taken: {worst_time}")
