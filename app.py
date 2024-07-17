import streamlit as st
import pyaudio
import asyncio
import wave
from deepgram import DeepgramClientOptions, DeepgramClient, LiveOptions, LiveTranscriptionEvents

# Initialize Deepgram client
config = DeepgramClientOptions(
    options={"keepalive": "true"}
)
deepgram = DeepgramClient('api key', config)
dg_connection = deepgram.listen.websocket.v("1")

# Initialize session state
if 'result' not in st.session_state:
    st.session_state['result'] = 'placeholder'

if 'stop' not in st.session_state:
    st.session_state['stop'] = True

# Callback function to handle transcription result
def on_message(self,result, **kwargs):
    sentence = result.channel.alternatives[0].transcript
    if len(sentence) == 0:
        return
    print(sentence)
    st.session_state['result'] = sentence
    st.rerun()  # Trigger Streamlit to update

# Display transcription result
def print_transcription():
    st.write(st.session_state['result'])

# Configure Deepgram connection
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

options = LiveOptions(
    model="nova-2",
    punctuate=True,
    language="en-US",
    encoding="linear16",
    channels=1,
    sample_rate=16000,
    interim_results=True,
    utterance_end_ms="1000",
    vad_events=True,
)

def main():
    title = st.title("Deepgram Live Transcription with Streamlit")
    print_transcription()
    if not st.session_state['stop']:
        if st.button("Stop Recording"):
            st.session_state['stop'] = True
    else:
        if st.button("Start Recording"):
            st.session_state['stop'] = False
            asyncio.run(start_recording())

async def start_recording():
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)

    wf = wave.open("recorded_audio.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)

    dg_connection.start(options)

    while not st.session_state.get('stop', False):
        audio_data = stream.read(1024)
        wf.writeframes(audio_data)
        dg_connection.send(audio_data)
        await asyncio.sleep(0.1)

    stream.stop_stream()
    stream.close()
    p.terminate()
    dg_connection.finish()
    wf.close()

if __name__ == "__main__":
    main()
