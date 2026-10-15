# EcoSort — Smart Waste Segregation Using Machine Learning

Prototype for Team Quantum Coders, Sri Sairam College of Engineering.

## Features
- Upload JPG, PNG, or WEBP waste-item images.
- Predicts a likely category among Plastic, Paper, Metal, Glass, and Organic.
- Shows model score, alternative category rankings, and disposal guidance.
- Warns users that uncertain or unusual items require manual verification.
- Responsive Streamlit interface.

## Stack
- Python
- Streamlit
- Hugging Face Transformers
- OpenAI CLIP pretrained vision-language model
- PyTorch and Pillow

## Run on Windows
1. Install Python 3.10 or 3.11 and make sure **Add Python to PATH** is selected.
2. Extract this folder.
3. Open the folder in VS Code.
4. Open Terminal → New Terminal.
5. Run:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```

6. The app opens in your browser, usually at `http://localhost:8501`.

If PowerShell blocks activation, run this in the same terminal:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
Then activate the environment again.

## First run
The CLIP model downloads from Hugging Face on the first analysis. A stable internet connection is required, and the first run may take several minutes. Subsequent runs use the cached model.

## Important limitations
- This is a rapid prototype using a general pretrained image-language model, not a model trained or validated specifically on a waste dataset.
- The displayed score is a relative model score, not validated classification accuracy or a calibrated probability.
- The prototype has not been evaluated on a held-out waste dataset. Do not claim a measured accuracy until proper testing is completed.
- Disposal guidance is general; local municipal rules take priority.
- It is intended for demonstration and awareness, not hazardous-waste identification.

## Suggested showcase demo
1. Test with a clean plastic bottle.
2. Test with a sheet of paper or cardboard.
3. Test with a metal can.
4. Test with a glass jar.
5. Test with fruit peel.
6. Discuss limitations and explain that dataset-specific training and evaluation are the next development steps.

## Architecture
Image upload → Streamlit UI → CLIP image-text comparison → ranked material category → disposal guidance → result display.
