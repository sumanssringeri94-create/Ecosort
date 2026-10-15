@echo off
title EcoSort - Smart Waste Segregation
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause
