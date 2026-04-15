#!/bin/bash
cd /home/felipemonsalve28/g9_production/
source venv/bin/activate
python3 engine.py >> logs/trading.log 2>&1
