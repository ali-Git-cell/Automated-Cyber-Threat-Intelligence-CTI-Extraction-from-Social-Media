import os
import re
import time
import json
import asyncio
import pandas as pd
import nest_asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Allow nested event loops (important if running inside notebooks)
nest_asyncio.apply()


# ========= CONFIG (replace with .env values later if you want) =========
USERNAME = os.getenv("TELEGRAM_USERNAME")  # optional
PHONE = os.getenv("TELEGRAM_PHONE")
API_ID = os.getenv("TELEGRAM_API_ID")   # get from my.telegram.org
API_HASH = os.getenv("TELEGRAM_API_HASH")

#print("API_ID:", os.getenv("TELEGRAM_API_ID"))
#print("API_HASH:", os.getenv("TELEGRAM_API_HASH"))

CHANNELS = [c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "@thehackernews").split(",")]

DATE_MIN = datetime.fromisoformat(os.getenv("TELEGRAM_DATE_MIN", "2025-08-15")).replace(tzinfo=timezone.utc)
DATE_MAX = datetime.fromisoformat(os.getenv("TELEGRAM_DATE_MAX", "2025-09-15")).replace(tzinfo=timezone.utc)

FILE_NAME = os.getenv("TELEGRAM_FILE_NAME", "Test-CTI-extraction")
KEY_SEARCH = os.getenv("TELEGRAM_KEYWORD", "")
MAX_T_INDEX = int(os.getenv("TELEGRAM_MAX_INDEX", "20000"))
TIME_LIMIT = int(os.getenv("TELEGRAM_TIME_LIMIT", "21600"))  # default 6 hours
FILE_FORMAT = os.getenv("TELEGRAM_FILE_FORMAT", "parquet").lower()  # "parquet" or "excel"


# ========= HELPERS =========
def remove_unsupported_characters(text: str) -> str:
    """Remove invalid XML characters from text."""
    if not text:
        return ""
    valid_xml_chars = (
        "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD"
        "\U00010000-\U0010FFFF]"
    )
    return re.sub(valid_xml_chars, "", text)


def format_time(seconds: int) -> str:
    """Format time in dd:hh:mm:ss format."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(days):02}:{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def print_progress(t_index, message_id, start_time, max_t_index):
    elapsed_time = time.time() - start_time
    current_progress = t_index / max(1, (t_index + message_id)) if (t_index + message_id) <= max_t_index else t_index / max_t_index
    percentage = current_progress * 100
    estimated_total_time = elapsed_time / max(0.0001, current_progress)
    remaining_time = estimated_total_time - elapsed_time

    elapsed_time_str = format_time(elapsed_time)
    remaining_time_str = format_time(remaining_time)

    print(f"Progress: {percentage:.2f}% | Elapsed Time: {elapsed_time_str} | Remaining Time: {remaining_time_str}")


# ========= MAIN SCRAPER =========
async def scrape():
    data = []
    t_index = 0
    start_time = time.time()

    for channel in CHANNELS:
        if t_index >= MAX_T_INDEX or (time.time() - start_time) > TIME_LIMIT:
            break

        try:
            c_index = 0
            async with TelegramClient(USERNAME, API_ID, API_HASH) as client:
                async for message in client.iter_messages(channel, search=KEY_SEARCH):
                    try:
                        if DATE_MIN <= message.date <= DATE_MAX:
                            content = remove_unsupported_characters(message.text)
                            emoji_string = ""

                            if message.reactions:
                                for reaction_count in message.reactions.results:
                                    emoji = reaction_count.reaction.emoticon
                                    count = str(reaction_count.count)
                                    emoji_string += emoji + " " + count + " "

                            date_time = message.date.strftime("%Y-%m-%d %H:%M:%S")

                            data.append({
                                "Type": "text",
                                "Group": channel,
                                "Content": content,
                                "Date": date_time,
                                "Message ID": message.id,
                                "Views": message.views,
                                "Reactions": emoji_string,
                                "Shares": message.forwards,
                            })

                            c_index += 1
                            t_index += 1

                            # Print progress
                            print("-" * 80)
                            print_progress(t_index, message.id, start_time, MAX_T_INDEX)
                            print(f"From {channel}: {c_index:05} messages processed")
                            print(f"ID: {message.id:05} / Date: {date_time}")
                            print(f"Total so far: {t_index:05}")
                            print("-" * 80)

                            if t_index % 1000 == 0:
                                backup_filename = f"backup_{FILE_NAME}_{t_index:05}_{channel}.{'parquet' if FILE_FORMAT=='parquet' else 'xlsx'}"
                                df_backup = pd.DataFrame(data)
                                if FILE_FORMAT == "parquet":
                                    df_backup.to_parquet(backup_filename, index=False)
                                else:
                                    df_backup.to_excel(backup_filename, index=False, engine="openpyxl")

                            if t_index >= MAX_T_INDEX or (time.time() - start_time) > TIME_LIMIT:
                                break

                        elif message.date < DATE_MIN:
                            break

                    except Exception as e:
                        print(f"Error processing message {message.id}: {e}")

            print(f"##### {channel} completed with {c_index:05} posts #####")

            df = pd.DataFrame(data)
            partial_filename = f"complete_{channel}_{FILE_NAME}_{t_index:05}.{'parquet' if FILE_FORMAT=='parquet' else 'xlsx'}"
            if FILE_FORMAT == "parquet":
                df.to_parquet(partial_filename, index=False)
            else:
                df.to_excel(partial_filename, index=False, engine="openpyxl")

        except Exception as e:
            print(f"{channel} error: {e}")

        time.sleep(2)  # to avoid rate limits

    df = pd.DataFrame(data)
    final_filename = f"FINAL_{FILE_NAME}_with_{t_index:05}.{'parquet' if FILE_FORMAT=='parquet' else 'xlsx'}"
    if FILE_FORMAT == "parquet":
        df.to_parquet(final_filename, index=False)
    else:
        df.to_excel(final_filename, index=False, engine="openpyxl")

    print(f"✅ Saved final file: {final_filename}")
    return df, final_filename


# Entry point if run directly
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    df, filename = loop.run_until_complete(scrape())
    print(f"Scraping done. File saved at: {filename}")
