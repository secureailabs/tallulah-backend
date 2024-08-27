# type: ignore

import asyncio
import xml.etree.ElementTree as ET
from typing import Callable, Dict, Optional

import aiohttp
from pydantic import BaseModel


class AccountInfo(BaseModel):
    id: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    middleName: Optional[str] = None
    suffix: Optional[str] = None
    initials: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phones: Optional[str] = None
    socialMediaProfiles: Optional[str] = None
    address: Optional[str] = None
    streetName: Optional[str] = None
    apartmentNumber: Optional[str] = None
    buildingNumber: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    suburb: Optional[str] = None
    webAddress: Optional[str] = None
    title: Optional[str] = None
    donorRecognitionName: Optional[str] = None
    donorRecognitionType: Optional[str] = None
    envelopeSalutation: Optional[str] = None
    longSalutation: Optional[str] = None
    shortSalutation: Optional[str] = None
    nameFormat: Optional[str] = None
    sortName: Optional[str] = None
    accountCreatedDate: Optional[str] = None
    accountLastModifiedDate: Optional[str] = None
    personaCreatedDate: Optional[str] = None
    personaLastModifiedDate: Optional[str] = None
    optOutDate: Optional[str] = None
    optedOut: Optional[str] = None
    accountRoleType: Optional[str] = None
    personaType: Optional[str] = None
    personaTypes: Optional[str] = None
    primaryPersona: Optional[str] = None
    donorRoleRef: Optional[str] = None
    teamRoleRef: Optional[str] = None
    tributeRoleRef: Optional[str] = None
    userRoleRef: Optional[str] = None
    ref: Optional[str] = None
    note: Optional[str] = None
    defined_values: Optional[Dict[str, str]] = None
    accountDefinedValues: Optional[str] = None
    personaDefinedValues: Optional[str] = None
    oldFormattedAddress: Optional[str] = None
    stickyNoteType: Optional[str] = None


class Etapestry:
    def __init__(self, database_id: str, api_key: str):
        self.url = "https://bos.etapestry.com/v3messaging/service"
        self.database_id = database_id
        self.api_key = api_key

    async def login(self):
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>\n<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns="etapestryAPI/service">\n    <SOAP-ENV:Body>\n        <tns:apiKeyLogin xmlns:tns="etapestryAPI/service">\n            <String_1 xsi:type="xsd:string">{self.database_id}</String_1>\n            <String_2 xsi:type="xsd:string">{self.api_key}</String_2>\n        </tns:apiKeyLogin>\n    </SOAP-ENV:Body>\n</SOAP-ENV:Envelope>"""
        headers = {"Content-Type": "text/xml; charset=UTF-8", "User-Agent": "NuSOAP/0.9.5 (1.123)", "SOAPAction": '""'}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, data=payload) as response:
                cookies = response.cookies
                if "JSESSIONID" not in cookies and "NSC_WJQ-FUBQFTUSZ-ENA" not in cookies:
                    raise Exception("Login failed")
                self.cookies = f"JSESSIONID={cookies["JSESSIONID"].value}; NSC_WJQ-FUBQFTUSZ-ENA={cookies["NSC_WJQ-FUBQFTUSZ-ENA"].value}"

    async def get_accounts(self, callback: Callable, *args, **kwargs):
        if not hasattr(self, "cookies"):
            await self.login()

        count = 200
        skip = 0
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "Cookie": self.cookies
        }

        while True:
            payload = f"""<?xml version="1.0" encoding="UTF-8"?>\n<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:tns="etapestryAPI/service">\n    <SOAP-ENV:Body>\n        <tns:getExistingQueryResults xmlns:tns="etapestryAPI/service">\n            <PagedExistingQueryResultsRequest_1 xsi:type="tns:PagedExistingQueryResultsRequest">\n                <count xsi:type="xsd:int">{count}</count>\n                <start xsi:type="xsd:int">{skip}</start>\n                <query xsi:type="xsd:string">Recipients::Recipients</query>\n            </PagedExistingQueryResultsRequest_1>\n        </tns:getExistingQueryResults>\n    </SOAP-ENV:Body>\n</SOAP-ENV:Envelope>"""

            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, data=payload) as response:
                    tasks = []

                    xml_data = await response.text()
                    root = ET.fromstring(xml_data)

                    result_count_respose = root.find('.//ns0:PagedQueryResultsResponse', namespaces={'ns0': 'etapestryAPI/service'})
                    if not result_count_respose:
                        break
                    result_count = result_count_respose.find('count').text
                    if result_count == '0':
                        break

                    for account in root.findall('.//ns0:Account', namespaces={'ns0': 'etapestryAPI/service'}):
                        id = account.attrib.get('id')
                        account_defined_values_id=account.find('accountDefinedValues').attrib.get('href'),
                        array_of_defined_values = root.find(f'.//ns0:ArrayOfDefinedValue[@id="{account_defined_values_id[0][1:]}"]', namespaces={'ns0': 'etapestryAPI/service'})
                        defined_values = {}
                        for defined_value_item in array_of_defined_values.findall('item'):
                            defined_value_id = defined_value_item.attrib.get('href')
                            defined_value = root.find(f'.//ns0:DefinedValue[@id="{defined_value_id[1:]}"]', namespaces={'ns0': 'etapestryAPI/service'})
                            defined_values[defined_value.find('fieldName').text] = defined_value.find('value').text

                        tasks.append(self.process_accounts(account, defined_values, callback, *args, **kwargs))

                    count = 200
                    skip += 200

                    await asyncio.gather(*tasks)


    async def process_accounts(self, account: ET.Element, defined_values: Dict[str, str], callback: Callable, *args, **kwargs):
        remove_from_defined_values = [
            "2019 Annual Appeal letters",
            "2020 Annual Appeal letters",
            "2021 Annual Appeal letters",
            "2022 Annual Appeal letters",
            "2023 Annual Appeal letters",
            "2024 Annual Appeal letters",
            "Target Analytics Discretionary Spending",
            "Target Analytics Wealth Segmentation",
            "Target Analytics Investments",
            "Target Analytics Net Worth",
            "Target Analytics Income"
        ]
        for key in remove_from_defined_values:
            defined_values.pop(key, None)

        account_info = AccountInfo(
            accountCreatedDate=account.find('accountCreatedDate').text,
            accountDefinedValues=account.find('accountDefinedValues').text,
            accountLastModifiedDate=account.find('accountLastModifiedDate').text,
            accountRoleType=account.find('accountRoleType').text,
            address=account.find('address').text,
            apartmentNumber=account.find('apartmentNumber').text,
            buildingNumber=account.find('buildingNumber').text,
            city=account.find('city').text,
            country=account.find('country').text,
            county=account.find('county').text,
            donorRecognitionName=account.find('donorRecognitionName').text,
            donorRecognitionType=account.find('donorRecognitionType').text,
            donorRoleRef=account.find('donorRoleRef').text,
            email=account.find('email').text,
            envelopeSalutation=account.find('envelopeSalutation').text,
            firstName=account.find('firstName').text,
            id=account.find('id').text,
            initials=account.find('initials').text,
            lastName=account.find('lastName').text,
            longSalutation=account.find('longSalutation').text,
            middleName=account.find('middleName').text,
            name=account.find('name').text,
            nameFormat=account.find('nameFormat').text,
            note=account.find('note').text,
            oldFormattedAddress=account.find('oldFormattedAddress').text,
            optOutDate=account.find('optOutDate').text,
            optedOut=account.find('optedOut').text,
            personaCreatedDate=account.find('personaCreatedDate').text,
            personaDefinedValues=account.find('personaDefinedValues').text,
            personaLastModifiedDate=account.find('personaLastModifiedDate').text,
            personaType=account.find('personaType').text,
            personaTypes=account.find('personaTypes').text,
            phones=account.find('phones').text,
            postalCode=account.find('postalCode').text,
            primaryPersona=account.find('primaryPersona').text,
            ref=account.find('ref').text,
            shortSalutation=account.find('shortSalutation').text,
            socialMediaProfiles=account.find('socialMediaProfiles').text,
            sortName=account.find('sortName').text,
            state=account.find('state').text,
            stickyNoteType=account.find('stickyNoteType').text,
            streetName=account.find('streetName').text,
            suburb=account.find('suburb').text,
            suffix=account.find('suffix').text,
            teamRoleRef=account.find('teamRoleRef').text,
            title=account.find('title').text,
            tributeRoleRef=account.find('tributeRoleRef').text,
            userRoleRef=account.find('userRoleRef').text,
            webAddress=account.find('webAddress').text,
            defined_values=defined_values
        )
        await callback(account_info, *args, **kwargs)
