import cv2
from utils import classify_image
  
# Init model
model = cv2.dnn.readNetFromONNX(
    "classifier.onnx")

vid = cv2.VideoCapture(0)
  
while(True):

    ret, frame = vid.read()

    result = classify_image(frame, model)
    cv2.putText(frame, result, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
  
    cv2.imshow('frame', frame)
      
    # the 'q' button is set as the
    # quitting button you may use any
    # desired button of your choice
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
  
# After the loop release the cap object
vid.release()
# Destroy all the windows
cv2.destroyAllWindows()
