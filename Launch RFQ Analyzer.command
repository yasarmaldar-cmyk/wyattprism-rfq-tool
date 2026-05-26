#!/bin/bash
cd "/Users/yasir/Yasar/AI Projects/rfq-tool"
echo "Starting RFQ Analyzer..."
echo "Opening browser at http://localhost:8505"
open "http://localhost:8505" &
streamlit run app.py --server.port 8505 --server.headless true
