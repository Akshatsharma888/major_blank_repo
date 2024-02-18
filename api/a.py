from flask import Flask, request, jsonify, make_response,render_template
from openai import OpenAI
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Replace "YOUR_API_KEY" with your actual OpenAI API key
client = OpenAI(api_key="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")

def generate_summary(text, model="gpt-3.5-turbo", max_tokens=150):

    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
            {"role": "system", "content": "can you plsease generate a more professional summary approx 100 words"},
            {"role": "user", "content": text}
        ],
    temperature=0.7,
    max_tokens=50,
    top_p=1

    )
    # Assuming 'response' contains the ChatCompletion object
    # summary_text = response# Assuming 'response' contains the ChatCompletion object
    summary_text = response.choices[0].message.content


    return summary_text

def generate_mcq_from_text(text, model="gpt-3.5-turbo", num_questions=5):
    mcqs = set()
    while len(mcqs) < num_questions:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "can you please generate MCQs from this text and include the correct answers as well?"},
                {"role": "user", "content": text}
            ],
            max_tokens=150,
            n=num_questions,
            stop=None,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        for choice in response.choices:
            content = choice.message.content.strip()
            mcqs.add(content)

    return list(mcqs)

@app.route('/')
def index():
    return render_template('index.html', questions='')
@app.route('/generate-questions', methods=['POST'])
def generate_questions():
    # Get the video file from the request
    video_file = request.files['video']
    video_file.save("input_video.mp4")

    # Load the video clip
    video_clip = VideoFileClip("input_video.mp4")

    # Extract audio from the video clip
    audio_clip = video_clip.audio

    # Specify the output audio file name
    output_audio_path = "speech.mp3"

    # Write the audio to a WAV file
    audio_clip.write_audiofile(output_audio_path)

    # Close the video clip to release resources
    video_clip.close()

    # Open the audio file in binary read mode
    audio_file = open("speech.mp3", "rb")

    # Create a transcription of the audio file
    transcript = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="text"
    )

    # Close the audio file
    audio_file.close()

    # Extract the transcript text from the response
    # transcript_text = transcript.choices[0].message.content  # Modified line
    
    # Summarize the transcript text
    summary_text = generate_summary(transcript)

    # Set the model you want to use
    model = "gpt-3.5-turbo"

    # Generate MCQs from the text
    mcqs = generate_mcq_from_text(transcript, model)

    # Create a list of dictionaries containing questions and their correct answers
    # Create a list of dictionaries containing questions and their correct answers
    questions_with_answers = []
    for mcq in mcqs:
        # Split the string into individual questions
        questions_and_answers = mcq.split("\n\n")
        for qa in questions_and_answers:
            # Split each question and answer pair into question text and correct answer
            qa_split = qa.split("\nAnswer: ")
            if len(qa_split) == 2:  # Ensure both question and answer are present
                question_text = qa_split[0]
                correct_answer = qa_split[1]
                # Format the correct answer
                correct_answer = correct_answer.strip().upper() + ")"
                questions_with_answers.append({"text": question_text, "correct_answer": correct_answer})

    # Return the generated questions, summary, and answers as JSON response
    response_data = jsonify({"questions": questions_with_answers,"summary":summary_text})
    response = make_response(response_data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    app.run(debug=True)
