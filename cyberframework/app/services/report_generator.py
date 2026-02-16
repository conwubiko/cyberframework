"""Report generation service — HTML and PDF reports."""
import os
from datetime import datetime, timezone
from flask import render_template, current_app
from app.models.assessment import Assessment
from app.models.report import Report
from app.services.scoring import get_assessment_results
from app.data.framework_controls import CROF_FUNCTIONS
from app.extensions import db


def generate_report(assessment_id, user_id, fmt='pdf'):
    """Generate an HTML or PDF report for a completed assessment."""
    assessment = Assessment.query.get(assessment_id)
    if not assessment or assessment.status != 'completed':
        return None

    responses = [
        {'control_id': r.control_id, 'function_id': r.function_id, 'answer': r.answer}
        for r in assessment.responses.all()
    ]
    results = get_assessment_results(responses)
    response_map = {r.control_id: r for r in assessment.responses.all()}

    html_content = render_template('report/report_pdf.html',
                                   assessment=assessment,
                                   results=results,
                                   response_map=response_map,
                                   functions=CROF_FUNCTIONS,
                                   generated_at=datetime.now(timezone.utc))

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    title = f"CROF Report - {assessment.title}"

    if fmt == 'pdf':
        try:
            from weasyprint import HTML
            filename = f"crof_report_{assessment_id}_{timestamp}.pdf"
            filepath = os.path.join(upload_dir, filename)
            HTML(string=html_content).write_pdf(filepath)
        except ImportError:
            # Fallback to HTML if weasyprint not available
            fmt = 'html'
            filename = f"crof_report_{assessment_id}_{timestamp}.html"
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
    else:
        filename = f"crof_report_{assessment_id}_{timestamp}.html"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

    report = Report(
        user_id=user_id,
        assessment_id=assessment_id,
        title=title,
        format=fmt,
        file_path=filepath,
    )
    db.session.add(report)
    db.session.commit()
    return report
