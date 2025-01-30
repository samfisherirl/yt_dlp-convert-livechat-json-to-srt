import json
from datetime import timedelta

def load_json_logs(filename, filter_users=None):  # Load JSON data from a file with optional username filtering
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    chat_entries = []
    for line in lines:
        data = json.loads(line)
        if 'replayChatItemAction' in data:
            actions = data['replayChatItemAction']['actions']
            for action in actions:
                if 'addChatItemAction' in action:
                    item = action['addChatItemAction']['item']
                    if 'liveChatTextMessageRenderer' in item:
                        msg_renderer = item['liveChatTextMessageRenderer']
                        username = msg_renderer.get('authorName', {}).get('simpleText', 'Unknown User')  # Get username
                        if filter_users and username not in filter_users:
                            continue  # Skip if filtering and username is not in filter list
                        video_offset_msec = int(data['replayChatItemAction']['videoOffsetTimeMsec'])
                        runs = msg_renderer['message']['runs']
                        try:
                            message = ''.join([run['text'] for run in runs])
                        except Exception as e:
                            continue
                        chat_entries.append((timedelta(milliseconds=video_offset_msec), username, message))
    return chat_entries

def seconds_to_srt_time(seconds):  # Formatting time for SRT
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03}"

def create_srt_entry(index, start_time, end_time, logs):  # Creating an SRT entry
    srt_texts = [f"{log[0].total_seconds()}s: {log[1]}: {log[2]}" for log in logs]  # Include username
    return f"{index}\n{seconds_to_srt_time(start_time)} --> {seconds_to_srt_time(end_time)}\n" + "\n".join(srt_texts) + "\n\n"

def generate_srt(chat_entries, srt_filename='chat_subtitles.srt'):  # Process and write to SRT file
    chat_entries.sort(key=lambda x: x[0])
    earliest_time = chat_entries[0][0]
    latest_time = chat_entries[-1][0]
    srt_entries = []
    index = 1
    start_time = 0
    current_logs = []

    for i in range(len(chat_entries)):
        log = chat_entries[i]
        log_time = log[0].total_seconds() - earliest_time.total_seconds()
        next_log_time = chat_entries[i + 1][0].total_seconds() - earliest_time.total_seconds() if i + 1 < len(chat_entries) else log_time + 20
        time_diff = next_log_time - log_time
        current_logs.append(log)

        if time_diff >= 20 or len(current_logs) > 3:  # Adjust these params for grouping
            end_time = log_time if time_diff >= 20 else next_log_time
            srt_entries.append(create_srt_entry(index, start_time, end_time, current_logs))
            current_logs = [] if time_diff >= 20 else current_logs[-3:]
            start_time = log_time if time_diff >= 20 else end_time
            index += 1

    if current_logs:
        srt_entries.append(create_srt_entry(index, start_time, latest_time.total_seconds() - earliest_time.total_seconds(), current_logs))

    with open(srt_filename, "w", encoding="utf-8") as srt_file:
        srt_file.writelines(srt_entries)

chat_entries = load_json_logs("logs.json", filter_users=['VoidAceX00'])
generate_srt(chat_entries)
