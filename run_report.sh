#!/bin/bash
cd /home/felipemonsalve28/g9_production/
source venv/bin/activate
python3 report.py >> logs/report.log 2>&1
