from flask import Flask, request, send_file
import io
import os
from datetime import datetime
from ParentsReports import Report

app = Flask(__name__)

@app.route('/generate-report', methods=['POST'])
def generate_report_endpoint():
    data = request.get_json()

    if not data or 'token' not in data:
        return {"error": "Token is required"}, 400

    user_token = data['token']

    try:
        report_text = Report(user_token)

        file_stream = io.BytesIO()
        file_stream.write(report_text.encode('utf-8'))
        file_stream.seek(0)

        from flask import Response

        return Response(
            report_text,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=child_weekly_report_{datetime.now().date()}.txt"
            }
        )

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))