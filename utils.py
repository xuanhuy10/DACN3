import cv2
import numpy as np

def classify_image(img, model):
    """Run classification on a given image.
    """
    classes = ['unknown', '10000', '20000', '50000']
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32)
    img = img / 255.0
    img = cv2.resize(img, (224, 224))
    img = np.expand_dims(img, axis=0)

    model.setInput(img)
    preds = model.forward()
    preds = preds[0]
    cls = preds.argmax()
    score = preds[cls]

    if score < 0.5:
        cls = 0

    return classes[cls]