import random
import re
import nltk
import spacy
from string import punctuation
from transcript import get_transcript_of_yt_video
from translate import g_translate
from download import makeTextFile
import pytube
from pytube import YouTube
nltk.download('stopwords')
import os
import requests

def text_summarizer(text):

    from heapq import nlargest
    from nltk.corpus import stopwords
    nlp = None
    try:
        nlp = spacy.load('en_core_web_sm')
    except:
        spacy.cli.download('en_core_web_sm')
        nlp = spacy.load('en_core_web_sm')
    stop_words = stopwords.words('english')

    doc = nlp(text)
    # tokens=[token.text for token in doc]

    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stop_words:
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1

    max_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word]/max_frequency

    sentence_tokens = [sent for sent in doc.sents]

    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]

    select_length = int(len(sentence_tokens)*0.3)
    summary = nlargest(select_length, sentence_scores, key=sentence_scores.get)

    summary = [re.sub('[.]', '', (word.text).replace(
        "\n", ",").strip()).capitalize() for word in summary]
    final_text = '. '.join(summary)

    final_summary = re.sub(',,|,\.|,\-|[\"]', '', final_text)

    return final_summary


def nlp_model(v_id,vid_url):

    transcript = get_transcript_of_yt_video(v_id)

    if (transcript == '0'):

        video_1 = YouTube(vid_url)
        if (video_1.age_restricted):
            return 0, 0,"Age Redistricted Video", "Age Redistricted Video", "Age Redistricted Video", "Age Redistricted Video"
        else:
            yt_1 = None
            try:
                yt_1 = video_1.streams.get_audio_only()
            except:
                yt_1 = video_1.streams.filter(only_audio=True).first()
            yt_1.download()
            current_dir = os.getcwd()
            for file in os.listdir(current_dir):
                if file.endswith(".mp4") or file.endswith(".mp3") :
                    mp4_file = os.path.join(current_dir, file)
                    # print(mp4_file)
            filename = mp4_file

            def read_file(filename, chunk_size=5242880):
                with open(filename, 'rb') as _file:
                    while True:
                        data = _file.read(chunk_size)
                        if not data:
                            break
                        yield data

            headers = {'authorization': '5eaf5de867704f889bc02a5c1ab16f95'}
            response = requests.post('https://api.assemblyai.com/v2/upload',
                                     headers=headers,
                                     data=read_file(filename))
            audio_url = response.json()['upload_url']

            # 3. Transcribe uploaded audio file
            endpoint = "https://api.assemblyai.com/v2/transcript"

            json = {
                "audio_url": audio_url
            }

            headers = {
                "authorization": '5eaf5de867704f889bc02a5c1ab16f95',
                "content-type": "application/json"
            }

            transcript_input_response = requests.post(endpoint, json=json, headers=headers)

            # 4. Extract transcript ID
            transcript_id = transcript_input_response.json()["id"]

            # 5. Retrieve transcription results
            endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            headers = {
                "authorization": '5eaf5de867704f889bc02a5c1ab16f95',
            }
            transcript_output_response = requests.get(endpoint, headers=headers)

            # 6. Check if transcription is complete
            from time import sleep

            while transcript_output_response.json()['status'] != 'completed':
                sleep(5)
                transcript_output_response = requests.get(endpoint, headers=headers)
            if (transcript_output_response.json()["text"] == ""):
                if os.path.exists(filename):
                    os.remove(filename)
                return 0, 0,"data not found", "data not found", "data not found", "data not found"
            else:
                org_summary = transcript_output_response.json()["text"]
                s_t = []
                s_t.append(text_summarizer(org_summary))
                english_summary = ' '.join(s_t) + '.'

                final_summary_length = len(english_summary)
                hindi_translated_summary = g_translate(english_summary, 'hi')
                marathi_translated_summary = g_translate(english_summary, 'mr')
                if os.path.exists(filename):
                    os.remove(filename)
                return len(org_summary), final_summary_length,org_summary, english_summary, hindi_translated_summary, marathi_translated_summary


    else:
        transcript_size = len(transcript)

        original_text = ' '.join([t['text'] for t in transcript])
        original_text_length = len(original_text)

        s_t = []

        result = ""

        for txt in range(0, transcript_size):
            if (txt != 0 and txt % 100 == 0):
                result += ' ' + transcript[txt]['text']
                s_t.append(text_summarizer(result))
                result = ""
            else:
                result += ' ' + transcript[txt]['text']

            if (txt == transcript_size - 1):
                result += ' ' + transcript[txt]['text']
                s_t.append(text_summarizer(result))

        english_summary = ' '.join(s_t) + '.'

        final_summary_length = len(english_summary)

        hindi_translated_summary = g_translate(english_summary, 'hi')

        marathi_translated_summary = g_translate(english_summary, 'mr')


        return original_text_length, final_summary_length,original_text, english_summary, hindi_translated_summary, marathi_translated_summary

