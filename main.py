from flask import Flask, render_template, request, Response, jsonify, send_file, after_this_request
import keras
import cv2
import numpy as np
import json
from keras.layers import *
import tensorflow as tf


app = Flask(__name__, template_folder='templates')

import cv2

camera = cv2.VideoCapture(0)
global start_button
start_button = False
global save_button
save_button = False

model = keras.models.load_model('model27.h5')
class_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'space']

def generate_frames():
    i = 0
    global start_button
    while start_button:
        
        ## read the camera frame
        success,frame=camera.read()
        i += 1
    
      
        frame = cv2.flip(frame,1)
        if not success:
            print('FAILED')
            break
        temp = frame[150:350, 50:250].copy()
        cv2.rectangle(frame, pt1=(50,150), pt2=(250,350), color=(0,255,0), thickness=10)

        if (i % 60 == 0):
            with open("static/data/log.json", "r") as jsonFile:
                data = json.load(jsonFile)
            print(i)

            temp = cv2.resize(temp, (256, 256))
            temp = temp[...,::-1].astype(np.float32)

            data["predict_label"],data["predict_prob"] = predict(temp)

            data["buffer_text"] += data["predict_label"]
            print(data)
            with open("static/data/log.json", "w") as jsonFile:
                json.dump(data, jsonFile)
           
        if not success:
            break
        else:
            # cv2.imwrite('static/data/crop.jpg', temp)

            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()

        yield(b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video')
def video():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_predict', methods = ['GET'])
def get_predict():
     with open("static/data/log.json", "r") as jsonFile:
            data = json.load(jsonFile)
     return jsonify({'predict_label': data["predict_label"],'predict_prob': data["predict_prob"], 'buffer_label': data["buffer_text"][-10:]})


@app.route('/')
def render_home():
    return render_template('home.html')

@app.route('/start_button', methods=['POST', 'GET'])
def toggle_start_button():
    global start_button
    global save_button
    start_button = True
    save_button = False
    return render_template('application.html')

@app.route('/stop_button', methods=['POST', 'GET'])
def toggle_stop_button():
    global start_button
    global save_button
    start_button = False
    save_button = False
    return render_template('application.html')

@app.route('/save_button', methods=['POST', 'GET'])
def toggle_save_button():
    with open("static/data/log.json", "r") as jsonFile:
        data = json.load(jsonFile)

    with open("static/data/output.txt", "w") as text_file:
        text_file.write(data["buffer_text"])
     
    data["predict_label"] = ""
    data["predict_prob"] = ""
    data["buffer_text"] = ""

    with open("static/data/log.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    global start_button
    global save_button
    save_button = True
    start_button =False

    return send_file("static/data/output.txt", as_attachment=True)

@app.route('/application')
def render_application():
    with open("static/data/log.json", "r") as jsonFile:
        data = json.load(jsonFile)
    
    data["predict_label"] = ""
    data["predict_prob"] = ""
    data["buffer_text"] = ""

    with open("static/data/log.json", "w") as jsonFile:
        json.dump(data, jsonFile)
    return render_template('application.html')

@app.route('/contact')
def render_contact():
    return render_template('contact.html')


def predict(img):
    input_arr = np.array([img])
    predict = model.predict(input_arr)
    prob = round(np.max(predict),2)
    if prob <0.7:
        return '',str(prob)

    result = class_names[np.argmax(predict)]
    return result, str(prob)



app.run(host="", port=50000, debug=True, use_reloader=False)