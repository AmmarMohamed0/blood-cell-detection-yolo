from flask import Flask, render_template, request, jsonify, send_file
from ultralytics import YOLO
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

model = YOLO("models/best.pt")

CLASS_NAMES = {
    0: "Platelets",
    1: "RBC",
    2: "WBC"
}

COLORS = {
    "Platelets" : (255, 215, 0),
    "RBC" : (220, 53, 69),
    "WBC" : (30, 144, 255)
}

OUTPUT_DIR = "static/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROCESSED_IMAGE = os.path.join(OUTPUT_DIR, "processed.jpg")
CHART_IMAGE = os.path.join(OUTPUT_DIR, "chart.png")
PDF_REPORT = os.path.join(OUTPUT_DIR, "blood_report.pdf")

latest_counts = {}
latest_boxes = {}

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    global latest_counts, latest_boxes

    file = request.files["image"]
    img_bytes = file.read()
    nping = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nping, cv2.IMREAD_COLOR)

    results = model(img)[0]

    counts = {name: 0 for name in CLASS_NAMES.values()}
    boxes_data = []

    h, w = img.shape[ :2]

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        class_name = CLASS_NAMES[cls_id]
        counts[class_name] += 1

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        color = COLORS[class_name]

        # Draw on image
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} {conf*100:.1f}%"
        cv2.putText(img, label, (x1, y1-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Save for frontend canvas
        boxes_data.append({
            "x": x1,
            "y": y1,
            "w": x2 - x1,
            "h": y2 - y1,
            "label": class_name,
            "confidence": round(conf * 100, 1),
            "color": f"rgb{color}"
        })

    cv2.imwrite(PROCESSED_IMAGE, img)

    latest_counts = counts
    latest_boxes = boxes_data

    return jsonify({
        "counts": counts,
        "boxes": boxes_data,
        "image": "/static/output/processed.jpg"
    })

def generate_chart(counts):
    plt.figure(figsize=(4, 3))
    plt.bar(counts.keys(), counts.values())
    plt.title("Blood Cell Distribution")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(CHART_IMAGE)
    plt.close()


def generate_pdf():
    doc = SimpleDocTemplate(PDF_REPORT, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI Hematology Analysis Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    date_str = datetime.now().strftime("%d %b %Y | %H:%M")
    story.append(Paragraph(f"Generated on: {date_str}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Processed Blood Smear Image</b>", styles["Heading2"]))
    story.append(RLImage(PROCESSED_IMAGE, width=400, height=250))
    story.append(Spacer(1, 14))

    table_data = [["Cell Type", "Count"]]
    for k, v in latest_counts.items():
        table_data.append([k, str(v)])

    story.append(Paragraph("<b>Detection Summary</b>", styles["Heading2"]))
    story.append(Table(table_data))
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Cell Distribution Chart</b>", styles["Heading2"]))
    story.append(RLImage(CHART_IMAGE, width=300, height=200))
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "This report is generated using an AI-based system and is intended "
        "for research and educational purposes only.",
        styles["Normal"]
    ))

    doc.build(story)

@app.route("/download-report")
def download_report():
    if not latest_counts:
        return "No report available. Please analyze an image first."
    
    generate_chart(latest_counts)
    generate_pdf()
    return send_file(PDF_REPORT, as_attachment=True)

# Main
if __name__ == "__main__":
    app.run(debug=True)