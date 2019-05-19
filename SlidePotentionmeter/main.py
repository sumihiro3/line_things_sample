from flask import Flask, request, abort
import json
import base64

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"
CHANNEL_SECRET = "<YOUR_CHANNEL_SECRET>"
line_bot_api = LineBotApi(ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)

data_store = {}

@app.route("/")
def healthcheck():
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # Python SDK doesn't support LINE Things event
        # => Unknown event type. type=things
        for event in parser.parse(body, signature):
            handle_message(event)

        # Parse JSON without SDK for LINE Things event
        events = json.loads(body)
        for event in events["events"]:
            print("Event: %s", event)
            if "things" in event:
                handle_things_event(event)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def handle_things_event(event):
    if event["things"]["type"] != "scenarioResult":
        return
    if event["things"]["result"]["resultCode"] != "success":
        app.logger.warn("Error result: %s", event)
        return
    user_id = event["source"]["userId"]
    last_state = data_store.get(user_id, None)
    state = int.from_bytes(base64.b64decode(event["things"]["result"]["bleNotificationPayload"]), 'little')
    # compare previos state
    if state != last_state:
        if state == 1:
            msg = "いってきま〜す！"
        else:
            msg = "ただいま〜♪"
        data_store[user_id] = state
        line_bot_api.reply_message(event["replyToken"], TextSendMessage(text=msg))

def handle_message(event):
    if event.type == "message" and event.message.type == "text":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
