import os
import re
from datetime import timedelta
from dental import app, db, Scan, PainAssessment, AnesthesiaPrediction, Consultation, clean_thinking_text

def clean_and_update_database():
    """
    Cleans up existing database records in dentalinsight MySQL DB:
    1. Removes any <think>...</think> or unclosed <think> reasoning blocks from summary and analysis columns.
    2. Adjusts past UTC created_at timestamps to IST by adding 5 hours 30 minutes.
    """
    with app.app_context():
        print("Starting database cleanup for existing records...")

        # 1. Clean Scans table
        scans = Scan.query.all()
        scan_count = 0
        for scan in scans:
            modified = False
            
            # Clean summary and analysis text
            if scan.summary:
                cleaned_summ = clean_thinking_text(scan.summary)
                if cleaned_summ != scan.summary:
                    scan.summary = cleaned_summ
                    modified = True
            
            if scan.analysis:
                cleaned_analysis = clean_thinking_text(scan.analysis)
                if cleaned_analysis != scan.analysis:
                    scan.analysis = cleaned_analysis
                    modified = True

            # Convert UTC timestamp to IST (+5h 30m offset) if needed
            # (assuming timestamps were recorded in UTC previously)
            if scan.created_at:
                scan.created_at = scan.created_at + timedelta(hours=5, minutes=30)
                modified = True

            if modified:
                scan_count += 1

        # 2. Clean Pain Assessments
        pains = PainAssessment.query.all()
        pain_count = 0
        for pain in pains:
            modified = False
            if pain.advice:
                cleaned_advice = clean_thinking_text(pain.advice)
                if cleaned_advice != pain.advice:
                    pain.advice = cleaned_advice
                    modified = True
            if pain.created_at:
                pain.created_at = pain.created_at + timedelta(hours=5, minutes=30)
                modified = True
            if modified:
                pain_count += 1

        # 3. Clean Anesthesia Predictions
        anesthesias = AnesthesiaPrediction.query.all()
        anest_count = 0
        for anest in anesthesias:
            modified = False
            if anest.result:
                cleaned_res = clean_thinking_text(anest.result)
                if cleaned_res != anest.result:
                    anest.result = cleaned_res
                    modified = True
            if anest.created_at:
                anest.created_at = anest.created_at + timedelta(hours=5, minutes=30)
                modified = True
            if modified:
                anest_count += 1

        # 4. Clean Consultations
        consults = Consultation.query.all()
        consult_count = 0
        for consult in consults:
            modified = False
            if consult.reply:
                cleaned_reply = clean_thinking_text(consult.reply)
                if cleaned_reply != consult.reply:
                    consult.reply = cleaned_reply
                    modified = True
            if consult.created_at:
                consult.created_at = consult.created_at + timedelta(hours=5, minutes=30)
                modified = True
            if modified:
                consult_count += 1

        db.session.commit()
        print(f"Successfully updated:\n - {scan_count} Scans\n - {pain_count} Pain Assessments\n - {anest_count} Anesthesia Predictions\n - {consult_count} Consultations")

if __name__ == '__main__':
    clean_and_update_database()
