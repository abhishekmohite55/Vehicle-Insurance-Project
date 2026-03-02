from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run

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

class DataForm:
    def __init__(self, request: Request):
        self.request = request
        # These will hold the raw string values from the form
        self.Gender: Optional[str] = None
        self.Age: Optional[str] = None
        self.Driving_License: Optional[str] = None
        self.Region_Code: Optional[str] = None
        self.Previously_Insured: Optional[str] = None
        self.Annual_Premium: Optional[str] = None
        self.Policy_Sales_Channel: Optional[str] = None
        self.Vintage: Optional[str] = None
        self.Vehicle_Age: Optional[str] = None          # single dropdown value
        self.Vehicle_Damage: Optional[str] = None

    async def get_vehicle_data(self):
        form = await self.request.form()
        self.Gender = form.get("Gender")
        self.Age = form.get("Age")
        self.Driving_License = form.get("Driving_License")
        self.Region_Code = form.get("Region_Code")
        self.Previously_Insured = form.get("Previously_Insured")
        self.Annual_Premium = form.get("Annual_Premium")
        self.Policy_Sales_Channel = form.get("Policy_Sales_Channel")
        self.Vintage = form.get("Vintage")
        self.Vehicle_Age = form.get("Vehicle_Age")
        self.Vehicle_Damage = form.get("Vehicle_Damage")

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

@app.get("/", tags=["authentication"])
async def index(request: Request):
    return templates.TemplateResponse(
        "vehicledata.html", {"request": request, "context": "Rendering"}
    )

@app.get("/train")
async def trainRouteClient():
    try:
        train_pipeline = TrainPipeline()
        train_pipeline.run_pipeline()
        return Response("Training successful!!!")
    except Exception as e:
        return Response(f"Error Occurred! {e}")

@app.post("/")
async def predictRouteClient(request: Request):
    try:
        form = DataForm(request)
        await form.get_vehicle_data()

        # Convert string values to model‑ready integers/floats
        gender_int = map_gender(form.Gender)
        driving_int = map_yes_no(form.Driving_License)
        previously_insured_int = map_yes_no(form.Previously_Insured)
        vehicle_age_lt, vehicle_age_gt = map_vehicle_age(form.Vehicle_Age)
        damage_int = map_yes_no(form.Vehicle_Damage)

        vehicle_data = VehicleData(
            Gender=gender_int,
            Age=int(form.Age) if form.Age else 0,
            Driving_License=driving_int,
            Region_Code=float(form.Region_Code) if form.Region_Code else 0.0,
            Previously_Insured=previously_insured_int,
            Annual_Premium=float(form.Annual_Premium) if form.Annual_Premium else 0.0,
            Policy_Sales_Channel=float(form.Policy_Sales_Channel) if form.Policy_Sales_Channel else 0.0,
            Vintage=int(form.Vintage) if form.Vintage else 0,
            Vehicle_Age_lt_1_Year=vehicle_age_lt,
            Vehicle_Age_gt_2_Years=vehicle_age_gt,
            Vehicle_Damage_Yes=damage_int
        )

        vehicle_df = vehicle_data.get_vehicle_input_data_frame()
        model_predictor = VehicleDataClassifier()
        value = model_predictor.predict(dataframe=vehicle_df)[0]

        status = "✅ Interested in Insurance" if value == 1 else "❌ Not Interested"

        return templates.TemplateResponse(
            "vehicledata.html",
            {"request": request, "context": status},
        )
    except Exception as e:
        return {"status": False, "error": f"{e}"}

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)