from flask import Flask, request, jsonify
import os
import json
from ParentsReports import Report

app = Flask(__name__)

@app.route('/generate-report', methods=['POST'])
def generate_report_endpoint():
    data = request.get_json()

    # Validate input
    if not data or 'userId' not in data:
        return jsonify({
            "status": "error",
            "message": "userId is required"
        }), 400

    user_id = data['userId']

    try:
        # Generate report
        report_text = Report(user_id)

        # 👇 Handle error from Report
        if isinstance(report_text, dict) and "error" in report_text:
            return jsonify({
                "status": "error",
                "message": report_text["error"]
            }), 500

        # Convert string → JSON
        report_json = json.loads(report_text)

        return jsonify({
            "status": "success",
            "data": report_json
        })

    except json.JSONDecodeError:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON format from AI response"
        }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))