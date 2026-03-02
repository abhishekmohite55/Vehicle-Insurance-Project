// static/js/predict.js

// Get DOM elements
const formElements = {
    Gender: document.getElementById('Gender'),
    Age: document.getElementById('Age'),
    AgeVal: document.getElementById('AgeVal'),
    Driving_License: document.getElementById('Driving_License'),
    Region_Code: document.getElementById('Region_Code'),
    Region_CodeVal: document.getElementById('Region_CodeVal'),
    Previously_Insured: document.getElementById('Previously_Insured'),
    Annual_Premium: document.getElementById('Annual_Premium'),
    Annual_PremiumVal: document.getElementById('Annual_PremiumVal'),
    Policy_Sales_Channel: document.getElementById('Policy_Sales_Channel'),
    Policy_Sales_ChannelVal: document.getElementById('Policy_Sales_ChannelVal'),
    Vintage: document.getElementById('Vintage'),
    VintageVal: document.getElementById('VintageVal'),
    Vehicle_Age: document.getElementById('Vehicle_Age'),
    Vehicle_Damage: document.getElementById('Vehicle_Damage'),
    resultCard: document.getElementById('result-card'),
    resultText: document.getElementById('result-text')
};

// Update displayed values for sliders
function updateSliderValues() {
    formElements.AgeVal.textContent = formElements.Age.value;
    formElements.Region_CodeVal.textContent = parseFloat(formElements.Region_Code.value).toFixed(1);
    formElements.Annual_PremiumVal.textContent = formElements.Annual_Premium.value;
    formElements.Policy_Sales_ChannelVal.textContent = parseFloat(formElements.Policy_Sales_Channel.value).toFixed(1);
    formElements.VintageVal.textContent = formElements.Vintage.value;
}

// Debounce function to limit API calls
function debounce(func, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

// Collect all input values and send to /predict_json
async function fetchPrediction() {
    // Build data object with string values (as the Pydantic model expects)
    const data = {
        Gender: formElements.Gender.value,
        Age: parseInt(formElements.Age.value),
        Driving_License: formElements.Driving_License.value,
        Region_Code: parseFloat(formElements.Region_Code.value),
        Previously_Insured: formElements.Previously_Insured.value,
        Annual_Premium: parseFloat(formElements.Annual_Premium.value),
        Policy_Sales_Channel: parseFloat(formElements.Policy_Sales_Channel.value),
        Vintage: parseInt(formElements.Vintage.value),
        Vehicle_Age: formElements.Vehicle_Age.value,
        Vehicle_Damage: formElements.Vehicle_Damage.value
    };

    // Basic validation: ensure all selects have a value
    const requiredSelects = ['Gender', 'Driving_License', 'Previously_Insured', 'Vehicle_Age', 'Vehicle_Damage'];
    for (let id of requiredSelects) {
        if (!formElements[id].value) {
            // Don't call API if any dropdown is not selected
            return;
        }
    }

    try {
        const response = await fetch('/predict_json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.prediction !== undefined) {
            const isInterested = result.prediction === 1;
            formElements.resultText.textContent = isInterested ? '✅ Interested in Insurance' : '❌ Not Interested';
            formElements.resultCard.style.display = 'block';
        } else {
            console.error('Prediction error:', result.error);
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// Debounced version of fetchPrediction
const debouncedFetch = debounce(fetchPrediction, 300);

// Attach event listeners
formElements.Age.addEventListener('input', () => {
    updateSliderValues();
    debouncedFetch();
});
formElements.Region_Code.addEventListener('input', () => {
    updateSliderValues();
    debouncedFetch();
});
formElements.Annual_Premium.addEventListener('input', () => {
    updateSliderValues();
    debouncedFetch();
});
formElements.Policy_Sales_Channel.addEventListener('input', () => {
    updateSliderValues();
    debouncedFetch();
});
formElements.Vintage.addEventListener('input', () => {
    updateSliderValues();
    debouncedFetch();
});

// Dropdown changes
formElements.Gender.addEventListener('change', debouncedFetch);
formElements.Driving_License.addEventListener('change', debouncedFetch);
formElements.Previously_Insured.addEventListener('change', debouncedFetch);
formElements.Vehicle_Age.addEventListener('change', debouncedFetch);
formElements.Vehicle_Damage.addEventListener('change', debouncedFetch);

// Initial update of slider values
updateSliderValues();

// Optional: set default dropdown selections to avoid "select" prompt
// (You may want to set a default value in the HTML or via JS)