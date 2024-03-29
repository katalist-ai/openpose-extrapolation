import torch
from fastapi import FastAPI
from model import SkeletonExtrapolator
from vae import SkeletonVAE
from schema import InferenceRequest, Keypoint, InferenceResult
from paths import MODELS_DIR
from pathlib import Path
import os
import logging

logger = logging.getLogger('uvicorn')

model_name = os.environ.get('MODEL_NAME', 'v7-epoch=3-val_loss=0.001993.ckpt')
model_type = 'vae' if model_name.startswith('vae') else 'fcn'
logger.info(f'model_name: {model_name}')
best_model_path = Path(MODELS_DIR, model_name)

model = None
if model_type == 'vae':
    model = SkeletonVAE.load_from_checkpoint(best_model_path)
else:
    model = SkeletonExtrapolator.load_from_checkpoint(best_model_path)
model.eval()
model.to('cpu')

app = FastAPI()

@app.get("/")
def health():
    return "OK"

@app.post("/predict")
def predict(input: InferenceRequest) -> InferenceResult:
    x = []
    neck_points = []
    for body in input.keypoints:
        ps = []
        neckx = body[1].x
        necky = body[1].y
        neck_points.append([neckx, necky])
        for keypoint in body:
            if keypoint.visible:
                ps.extend([keypoint.x - neckx, keypoint.y - necky])
            else:
                ps.extend([-10.0, -10.0])
        x.append(ps)
    x = torch.tensor(x).to('cpu')
    with torch.no_grad():
        y_hat = model(x)
    keypoints = []
    for i, row in enumerate(y_hat):
        points = row.reshape(-1, 2).tolist()
        translated_points = []
        neckx, necky = neck_points[i]
        for point in points:
            translated_points.append(Keypoint(x=point[0] + neckx, y=point[1] + necky, visible=True))
        keypoints.append(translated_points)
    return {"keypoints": keypoints}
