# import modules
import torch
import os
import cv2
import numpy as np
from PIL import Image
import groundingdino.datasets.transforms as T
from groundingdino.util.inference import load_model, load_image, predict, annotate
from pythonosc import udp_client

# os.environ['CUDA_HOME'] = 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7'
# os.environ["CUDA_HOME"] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.7"

HOME = os.getcwd()
# set model configuration file path
CONFIG_PATH = os.path.join(
    HOME, "groundingdino\config\GroundingDINO_SwinB_cfg.py")

# wget -q https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
# or newer version
# get in weights folder

# set model weight file ath
WEIGHTS_NAME = "groundingdino_swinb_cogcoor.pth"
WEIGHTS_PATH = os.path.join(HOME, "weights", WEIGHTS_NAME)

# load model
# device = 'cuda' if torch.cuda.is_available() else 'cpu'
# print(f='Using device {device}')
model = load_model(CONFIG_PATH, WEIGHTS_PATH)
# model = model.to(device)

# set text prompt
TEXT_PROMPT = "cell phone . mobile phone . camera . "
# TEXT_PROMPT = "person with glasses. remote controller. "

# set box and text threshold values
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25


cap = cv2.VideoCapture(1)

OSC_IP = "10.0.0.32"
OSC_PORT = 12345
osc_client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)

transform = T.Compose(
    [
        T.RandomResize([500], max_size=600),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]
)

skip = 0
while True:
    skip +=1
    skip %=3
    if skip != 0:
        continue
    ret, frame = cap.read()
    # create a transform function by applying 3 image transaformations
    # convert frame to a PIL object in RGB space
    image_source = Image.fromarray(frame).convert("RGB")
    # convert the PIL image object to a transform object
    image_transformed, _ = transform(image_source, None)
    # image_transformed = image_transformed.to(device)

    # predict boxes, logits, phrases
    boxes, logits, phrases = predict(
        model=model,
        image=image_transformed,
        caption=TEXT_PROMPT,
        box_threshold=BOX_TRESHOLD,
        text_threshold=TEXT_TRESHOLD,
        device="cuda"
        )

    # annotate the image
    annotated_frame = annotate(
        image_source=frame, boxes=boxes, logits=logits, phrases=phrases)
    if not phrases:
        print("empty, show the drawing")
        osc_client.send_message("/hide",0)

    for item in phrases:
        print(item)
        if "phone" or "camera" in item:
            print("Hide the drawing")
            osc_client.send_message("/hide",1)
        

    # display the output
    out_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

    cv2.imshow('frame', out_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
