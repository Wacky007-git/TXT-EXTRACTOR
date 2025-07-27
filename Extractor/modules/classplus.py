import requests
import os
import json
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import CallbackQuery
from Extractor import app  # Assuming this is your Pyrogram Client instance
from config import SUDO_USERS

api = 'https://api.classplusapp.com/v2'

# ------------------------------------------------------------------------------------------------------------------------------- #

async def create_html_file(file_name, batch_name, contents):
    tbody = ''
    parts = contents.split('\n')
    for part in parts:
        split_part = [item.strip() for item in part.split(':', 1)]
        text = split_part[0] if split_part[0] else 'Untitled'
        url = split_part[1].strip() if len(split_part) > 1 and split_part[1].strip() else 'No URL'
        tbody += f'<tr><td>{text}</td><td><a href="{url}" target="_blank">{url}</a></td></tr>'

    async with asyncio.Lock():  # Async-safe file write
        with open('Extractor/core/template.html', 'r') as fp:
            file_content = fp.read()
        title = batch_name.strip()
        with open(file_name, 'w') as fp:
            fp.write(file_content.replace('{{tbody_content}}', tbody).replace('{{batch_name}}', title))

# ------------------------------------------------------------------------------------------------------------------------------- #

async def get_course_content(session, course_id, folder_id=0):
    fetched_contents = []
    params = {'courseId': course_id, 'folderId': folder_id}
    res = session.get(f'{api}/course/content/get', params=params)

    if res.status_code == 200:
        res = res.json()
        contents = res['data']['courseContent']
        for content in contents:
            if content['contentType'] == 1:
                resources = content['resources']
                if resources['videos'] or resources['files']:
                    sub_contents = await get_course_content(session, course_id, content['id'])
                    fetched_contents += sub_contents
            else:
                name = content['name']
                url = content['url']
                fetched_contents.append(f'{name}: {url}')
    return fetched_contents

async def classplus_txt(app, message, user_id):
    session = requests.Session()  # Create session inside to avoid global state
    headers = {
        'accept-encoding': 'gzip',
        'accept-language': 'EN',
        'api-version': '35',
        'app-version': '1.4.73.2',
        'build-number': '35',
        'connection': 'Keep-Alive',
        'content-type': 'application/json',
        'device-details': 'Xiaomi_Redmi 7_SDK-32',
        'device-id': 'c28d3cb16bbdac01',
        'host': 'api.classplusapp.com',
        'region': 'IN',
        'user-agent': 'Mobile-Android',
        'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c'
    }
    session.headers.update(headers)

    try:
        if user_id is None:
            raise ValueError("user_id cannot be None; it must be provided.")

        reply = await message.chat.ask(
            '**Send your credentials as shown below.\n\nOrganisation Code\nPhone Number\n\nOR\n\nAccess Token**',
            reply_to_message_id=message.id  # Use .id instead of .message_id for consistency
        )
        creds = reply.text

        logged_in = False

        if '\n' in creds:
            org_code, phone_no = [cred.strip() for cred in creds.split('\n')]
            if not (org_code.isalpha() and phone_no.isdigit() and len(phone_no) == 10):
                raise ValueError('Invalid credentials format.')

            res = session.get(f'{api}/orgs/{org_code}')
            if res.status_code != 200:
                raise Exception('Failed to get organization ID.')
            res = res.json()
            org_id = int(res['data']['orgId'])

            data = {
                'countryExt': '91',
                'mobile': phone_no,
                'viaSms': 1,
                'orgId': org_id,
                'eventType': 'login',
                'otpHash': 'j7ej6eW5VO'
            }
            res = session.post(f'{api}/otp/generate', data=json.dumps(data))
            if res.status_code != 200:
                raise Exception('Failed to generate OTP.')
            res = res.json()
            session_id = res['data']['sessionId']

            reply = await message.chat.ask('**Send OTP?**', reply_to_message_id=reply.id)
            if not reply.text.isdigit():
                raise ValueError('Invalid OTP.')
            otp = reply.text.strip()

            data = {
                'otp': otp,
                'sessionId': session_id,
                'orgId': org_id,
                'fingerprintId': 'a3ee05fbde3958184f682839be4fd0f7',
                'countryExt': '91',
                'mobile': phone_no,
            }
            res = session.post(f'{api}/users/verify', data=json.dumps(data))
            if res.status_code != 200:
                raise Exception('Failed to verify OTP.')
            res = res.json()
            token = res['data']['token']
            session.headers['x-access-token'] = token

            await reply.reply(f'**Your Access Token for future uses:**\n<pre>{token}</pre>', quote=True)
            logged_in = True

        else:
            token = creds.strip()
            session.headers['x-access-token'] = token
            res = session.get(f'{api}/users/details')
            if res.status_code != 200:
                raise Exception('Failed to get user details.')
            res = res.json()
            logged_in = True  # user_id is already provided; no need to re-fetch

        if not logged_in:
            raise Exception('Login failed.')

        params = {'userId': user_id, 'tabCategoryId': 3}
        res = session.get(f'{api}/profiles/users/data', params=params)
        if res.status_code != 200:
            raise Exception('Failed to get courses.')
        res = res.json()
        courses = res['data']['responseData']['coursesData']

        if not courses:
            raise Exception('No courses found.')

        text = '\n'.join(f'{cnt + 1}. {course["name"]}' for cnt, course in enumerate(courses))
        reply = await message.chat.ask(f'**Send index number of the course to download.\n\n{text}**', reply_to_message_id=reply.id)

        if not reply.text.isdigit() or not (1 <= int(reply.text) <= len(courses)):
            raise ValueError('Invalid course selection.')

        selected_course_index = int(reply.text.strip())
        course = courses[selected_course_index - 1]
        selected_course_id = course['id']
        selected_course_name = course['name']

        loader = await reply.reply('**Extracting course...**', quote=True)
        course_content = await get_course_content(session, selected_course_id)
        await loader.delete()

        if not course_content:
            raise Exception('No content found in course.')

        caption = f"App Name: Classplus\nBatch Name: {selected_course_name}"
        text_file = "Classplus"
        with open(f'{text_file}.txt', 'w') as f:
            f.write('\n'.join(course_content))

        await app.send_document(message.chat.id, document=f"{text_file}.txt", caption=caption)

        html_file = f'{text_file}.html'
        await create_html_file(html_file, selected_course_name, '\n'.join(course_content))  # Now async

        await app.send_document(message.chat.id, html_file, caption=caption)
        os.remove(f'{text_file}.txt')
        os.remove(html_file)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply(f'**Error: {e}**', quote=True)

# Command Handler for /extract
@app.on_message(filters.command("extract") & filters.user(SUDO_USERS))
async def extract_handler(client, message):
    user_id = message.from_user.id  # Properly derive user_id here
    await classplus_txt(app, message, user_id)  # Pass valid user_id

# Example Callback Handler Integration (from previous conversation)
@app.on_callback_query()  # Adjust filter as needed
async def handle_callback(app: Client, query: CallbackQuery):
    # ... other code ...
    elif query.data == "classplus_":
        user_id = query.from_user.id  # Extract user_id
        await classplus_txt(app, query.message, user_id)  # Consistent call
    # ... other code ...

# Start the bot
app.start()
idle()
