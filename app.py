from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run
from pydantic import BaseModel
import pandas as pd

from typing import Optional

from src.constants import APP_HOST, APP_PORT
from src.pipline.prediction_pipeline import VehicleData, VehicleDataClassifier
from src.pipline.training_pipeline import TrainPipeline

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='templates')

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Helper mapping functions (convert friendly strings to model integers)
# -------------------------------------------------------------------
def map_gender(value: str) -> int:
    return 1 if value and value.lower() == "male" else 0

def map_yes_no(value: str) -> int:
    return 1 if value and value.lower() == "yes" else 0

def map_vehicle_age(value: str):
    """Returns (lt_1_year, gt_2_years) flags."""
    if value == "< 1 Year":
        return (1, 0)
    elif value == "> 2 Years":
        return (0, 1)
    else:  # "1-2 Year" (reference category)
        return (0, 0)

# -------------------------------------------------------------------
# Pydantic model for JSON input (interactive endpoint)
# -------------------------------------------------------------------
class PredictionInput(BaseModel):
    Gender: str
    Age: int
    Driving_License: str
    Region_Code: float
    Previously_Insured: str
    Annual_Premium: float
    Policy_Sales_Channel: float
    Vintage: int
    Vehicle_Age: str
    Vehicle_Damage: str

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get("/", tags=["authentication"])
async def index(request: Request):
    """Render the main prediction form."""
    return templates.TemplateResponse(
        "vehicledata.html", {"request": request, "context": "Rendering"}
    )

@app.get("/train")
async def trainRouteClient():
    """Trigger the model training pipeline."""
    try:
        train_pipeline = TrainPipeline()
        train_pipeline.run_pipeline()
        return Response("Training successful!!!")
    except Exception as e:
        return Response(f"Error Occurred! {e}")

@app.post("/predict_json")
async def predict_json(input_data: PredictionInput):
    """
    AJAX endpoint – receives JSON with friendly values,
    converts them, runs prediction, and returns result as JSON.
    """
    try:
        # Convert friendly strings to model‑ready integers
        gender_int = map_gender(input_data.Gender)
        driving_int = map_yes_no(input_data.Driving_License)
        previously_int = map_yes_no(input_data.Previously_Insured)
        lt_1, gt_2 = map_vehicle_age(input_data.Vehicle_Age)
        damage_int = map_yes_no(input_data.Vehicle_Damage)

        # Build dictionary exactly as the model expects
        data_dict = {
            "Gender": gender_int,
            "Age": input_data.Age,
            "Driving_License": driving_int,
            "Region_Code": input_data.Region_Code,
            "Previously_Insured": previously_int,
            "Annual_Premium": input_data.Annual_Premium,
            "Policy_Sales_Channel": input_data.Policy_Sales_Channel,
            "Vintage": input_data.Vintage,
            "Vehicle_Age_lt_1_Year": lt_1,
            "Vehicle_Age_gt_2_Years": gt_2,
            "Vehicle_Damage_Yes": damage_int
        }

        df = pd.DataFrame([data_dict])
        model_predictor = VehicleDataClassifier()
        prediction = model_predictor.predict(df)[0]

        return {"prediction": int(prediction)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/")
async def predictRouteClient(request: Request):
    """
    Traditional form‑handling endpoint (fallback for non‑JavaScript).
    """
    try:
        # (Reuse the same DataForm class from before)
        # You can keep the original DataForm class here or import it.
        # For brevity, I'll sketch the essential steps – you already have it.
        # (Include your original DataForm and prediction logic here.)
        # After prediction, render the template with the result.
        pass
    except Exception as e:
        return {"status": False, "error": f"{e}"}

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)