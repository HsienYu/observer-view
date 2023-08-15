# import modules
import os
import cv2
import numpy as np
from PIL import Image
import groundingdino.datasets.transforms as T
from groundingdino.util.inference import load_model, load_image, predict, annotate


HOME = os.getcwd()
# set model configuration file path
CONFIG_PATH = os.path.join(
    HOME, "groundingdino/config/GroundingDINO_SwinT_OGC.py")

# wget -q https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
# or newer version
# get in weights folder

# set model weight file ath
WEIGHTS_NAME = "groundingdino_swint_ogc.pth"
WEIGHTS_PATH = os.path.join(HOME, "weights", WEIGHTS_NAME)

# load model

model = load_model(CONFIG_PATH, WEIGHTS_PATH)

# set text prompt
TEXT_PROMPT = "glass with lid"

# set box and text threshold values
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25


cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    # create a transform function by applying 3 image transaformations
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]
    )
    # convert frame to a PIL object in RGB space
    image_source = Image.fromarray(frame).convert("RGB")
    # convert the PIL image object to a transform object
    image_transformed, _ = transform(image_source, None)

    # predict boxes, logits, phrases
    boxes, logits, phrases = predict(
        model=model,
        image=image_transformed,
        caption=TEXT_PROMPT,
        box_threshold=BOX_TRESHOLD,
        text_threshold=TEXT_TRESHOLD,
        device='cpu')

    # annotate the image
    annotated_frame = annotate(
        image_source=frame, boxes=boxes, logits=logits, phrases=phrases)
    # display the output
    out_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('frame', out_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
