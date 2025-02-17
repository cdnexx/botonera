from flask import Flask, redirect, request, render_template, jsonify
import pygame
import os
import json


app = Flask(__name__)

AUDIO_PATH = "audios"
IMAGE_PATH = "static/images"
JSON_FILE = "files.json"


def get_audios():
    #  id, archivo, nombre, imagen
    with open(JSON_FILE, "r") as archivo:
        audios = json.load(archivo)

    return audios["files"]


def cargar_datos():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            return json.load(f)
    return {"files": []}


def save_audio_data(data):
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def buscar_por_id(lista, id_buscar):
    for elemento in lista:
        if elemento["id"] == id_buscar:
            return elemento
    return None


@app.route('/')
def home():
    return render_template('index.html', audios=get_audios())


@app.route('/play/<audio_id>')
def play_audio(audio_id):
    audio_id = int(audio_id)
    audio = buscar_por_id(get_audios(), audio_id)
    pygame.mixer.init()
    pygame.mixer.music.load(f"{AUDIO_PATH}/{audio['filename']}")
    pygame.mixer.music.set_volume(0.05)
    pygame.mixer.music.play()
    return redirect('/')


@app.route('/upload', methods=['POST'])
def upload_file():
    texto = request.form.get('audio_name')

    # Verificar si se envió un archivo de audio
    if 'audio' not in request.files:
        return "No se encontró el archivo de audio en la solicitud.", 400

    # Verificar si se envió una imagen
    if 'image' not in request.files:
        return "No se encontró la imagen en la solicitud.", 400

    audio = request.files['audio']
    image = request.files['image']

    if audio.filename == '':
        return "No se seleccionó ningún archivo de audio.", 400

    if image.filename == '':
        return "No se seleccionó ninguna imagen.", 400

    # Guardar el archivo en la carpeta especificada
    audio_path = AUDIO_PATH + '/' + str(audio.filename)
    image_path = IMAGE_PATH + '/' + str(image.filename)

    audio.save(audio_path)
    image.save(image_path)

    # Determinar el próximo ID
    datos = cargar_datos()
    max_id = max((file['id'] for file in datos['files']), default=-1)
    nuevo_id = max_id + 1

    # Crear el nuevo registro
    nuevo_registro = {
        "id": nuevo_id,
        "filename": audio.filename,
        "name": texto,
        "img": image.filename
    }

    datos['files'].append(nuevo_registro)

    save_audio_data(datos)

    return redirect('/')


@app.route('/edit/<int:audio_id>', methods=['POST'])
def edit_audio(audio_id):
    datos = cargar_datos()
    audio = buscar_por_id(datos['files'], audio_id)

    if not audio:
        return jsonify({'error': 'Botón no encontrado'}), 404

    new_name = request.form.get('audio_name')
    new_image = request.files.get('image')

    # Actualizar nombre
    if new_name:
        audio['name'] = new_name

    # Actualizar imagen
    if new_image and new_image.filename:
        old_image_path = os.path.join(IMAGE_PATH, audio['img'])
        if os.path.exists(old_image_path):
            os.remove(old_image_path)

        new_image_path = os.path.join(IMAGE_PATH, new_image.filename)
        new_image.save(new_image_path)
        audio['img'] = new_image.filename

    save_audio_data(datos)
    return redirect('/')


@app.route('/delete/<int:audio_id>', methods=['GET'])
def delete_audio(audio_id):
    data = cargar_datos()  # Carga los datos del archivo JSON
    # Encuentra el botón correspondiente
    audio = buscar_por_id(data['files'], audio_id)

    if not audio:
        return jsonify({"error": "Botón no encontrado"}), 404

    # Eliminar los archivos asociados
    audio_path = os.path.join(AUDIO_PATH, audio['filename'])
    image_path = os.path.join(IMAGE_PATH, audio['img'])

    pygame.mixer.quit()

    if os.path.exists(audio_path):
        os.remove(audio_path)
    if os.path.exists(image_path):
        os.remove(image_path)

    # Eliminar el botón del JSON
    data['files'] = [file for file in data['files'] if file['id'] != audio_id]
    save_audio_data(data)  # Guarda los datos actualizados

    return redirect('/')  # Redirige a la página principal


if __name__ == '__main__':
    app.run(debug=True)
