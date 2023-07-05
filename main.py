"""
This is a FastAPI app that serves as a webhook for LINE Messenger.
It uses the embedchain library to handle incoming messages and generate appropriate responses.
"""
# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys

import aiohttp

from fastapi import Request, FastAPI, HTTPException

from embedchain import App


from linebot import (
    AsyncLineBotApi, WebhookParser
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # read local .env file

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('ChannelSecret', None)
channel_access_token = os.getenv('ChannelAccessToken', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

app = FastAPI()
session = aiohttp.ClientSession()
async_http_client = AiohttpAsyncHttpClient(session)
line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
parser = WebhookParser(channel_secret)

# Embedchain App
naval_chat_bot = App()

# Add tools to the app
naval_chat_bot.add(
    "web_page", "https://tw.linebiz.com/column/LINEOA-2023-Price-Plan/")

naval_chat_bot.add(
    "web_page", "https://tw.linebiz.com/column/stepmessage/")

naval_chat_bot.add(
    "web_page", "https://tw.linebiz.com/column/LAP-Maximize-OA-Strategy/")


@app.post("/callback")
async def handle_callback(request: Request):
    """
    Handle the callback from LINE Messenger.

    This function validates the request from LINE Messenger, 
    parses the incoming events and sends the appropriate response.

    Args:
        request (Request): The incoming request from LINE Messenger.

    Returns:
        str: Returns 'OK' after processing the events.
    """
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid signature") from exc

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        tool_result = naval_chat_bot.query(
            event.message.text + " reply in zh-tw, result")

        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=tool_result)
        )

    return 'OK'
