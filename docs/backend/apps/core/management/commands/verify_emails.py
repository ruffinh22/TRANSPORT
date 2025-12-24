from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime
from typing import Optional

import requests
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Verify emails (single or CSV) using Verimail API and output results to CSV."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="Single email address to verify")
        parser.add_argument("--file", help="Path to input CSV (one email per line)")
        parser.add_argument("--delay", type=float, default=0.5, help="Delay in seconds between API calls")
        parser.add_argument("--out", help="Output CSV path (default: verified_<timestamp>.csv)")

    def handle(self, *args, **options):
        api_key = os.getenv("VERIMAIL_API_KEY")
        if not api_key:
            raise CommandError("VERIMAIL_API_KEY environment variable not set. Add it to your .env or export it.")

        email = options.get("email")
        file_path = options.get("file")
        delay = float(options.get("delay") or 0.5)
        out_path = options.get("out")

        if not email and not file_path:
            raise CommandError("Provide either --email or --file argument.")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if not out_path:
            out_path = f"verified_{timestamp}.csv"

        session = requests.Session()
        session.headers.update({"Accept": "application/json"})

        def verify_one(e: str) -> dict:
            url = "https://api.verimail.io/v3/verify"
            try:
                resp = session.get(url, params={"email": e, "key": api_key}, timeout=20)
            except requests.RequestException as exc:
                return {"email": e, "status": "error", "error": str(exc)}

            result = {"email": e, "status": "error", "http_status": resp.status_code}
            try:
                payload = resp.json()
            except ValueError:
                result.update({"error": "invalid_json_response", "text": resp.text})
                return result

            if resp.status_code == 200 and payload.get("status") == "success":
                result.update({
                    "status": "success",
                    "result": payload.get("result"),
                    "deliverable": payload.get("deliverable"),
                    "user": payload.get("user"),
                    "domain": payload.get("domain"),
                    "did_you_mean": payload.get("did_you_mean", ""),
                })
            else:
                # map common errors
                if resp.status_code == 401:
                    result.update({"status": "error", "error": "unauthorized - invalid key or key missing"})
                elif resp.status_code == 403:
                    result.update({"status": "error", "error": "forbidden - key inactive or quota exceeded"})
                else:
                    # include message if provided
                    result.update({"status": "error", "error": payload})

            return result

        # If single email: print result
        if email:
            self.stdout.write(f"Verifying: {email}")
            res = verify_one(email)
            # pretty print
            for k, v in res.items():
                self.stdout.write(f"{k}: {v}")
            return

        # If file: stream and write CSV
        if file_path:
            if not os.path.exists(file_path):
                raise CommandError(f"Input file not found: {file_path}")

            self.stdout.write(f"Reading from {file_path} and writing to {out_path}")
            with open(file_path, newline="", encoding="utf-8") as infp, open(out_path, "w", newline="", encoding="utf-8") as outf:
                reader = csv.reader(infp)
                writer = csv.writer(outf)
                # header
                writer.writerow(["email", "status", "result", "deliverable", "user", "domain", "did_you_mean", "http_status", "error"])

                for row in reader:
                    if not row:
                        continue
                    e = row[0].strip()
                    if not e:
                        continue
                    self.stdout.write(f"Verifying {e} ... ", ending="")
                    sys.stdout.flush()
                    res = verify_one(e)
                    writer.writerow([
                        res.get("email"),
                        res.get("status"),
                        res.get("result"),
                        res.get("deliverable"),
                        res.get("user"),
                        res.get("domain"),
                        res.get("did_you_mean"),
                        res.get("http_status"),
                        res.get("error") if res.get("status") == "error" else "",
                    ])
                    self.stdout.write("done")
                    time.sleep(delay)

            self.stdout.write(self.style.SUCCESS(f"Verification finished. Results saved to {out_path}"))
