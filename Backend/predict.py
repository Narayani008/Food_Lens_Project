import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image

MODEL_PATH = "model/food_freshness_model.h5"
model = tf.keras.models.load_model(MODEL_PATH)

IMG_SIZE = 224
CLASS_NAMES = ["Fresh", "Spoiled"]

def predict_image(img_path):
    img = image.load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0

    prediction = model.predict(img_array)[0][0]

    if prediction >= 0.5:
        return "Spoiled", float(prediction)
    else:
        return "Fresh", float(1 - prediction)
