#!/usr/bin/env python3
"""
deploy.py - Script tự động hóa deploy Mini LMS Cloud
Chạy sau khi LocalStack đã khởi động:
  python deploy.py
"""

import subprocess
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TERRAFORM_DIR = os.path.join(SCRIPT_DIR, "terraform")
FRONTEND_FILE = os.path.join(SCRIPT_DIR, "frontend", "index.html")
BUCKET_NAME = "mini-lms-documents"
AWS_ENDPOINT = "http://localhost:4566"


def run(cmd, cwd=None, capture=False):
    print(f"\n▶ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=capture, text=True
    )
    if result.returncode != 0:
        if capture:
            print(result.stderr)
        sys.exit(f"❌ Lệnh thất bại: {cmd}")
    return result.stdout if capture else ""


def main():
    print("=" * 60)
    print("  Mini LMS Cloud — Auto Deploy Script")
    print("=" * 60)

    # Bước 1: Terraform init + apply
    print("\n[1/4] Khởi tạo Terraform...")
    run("terraform init", cwd=TERRAFORM_DIR)

    print("\n[2/4] Tạo hạ tầng AWS (LocalStack)...")
    run("terraform apply -auto-approve", cwd=TERRAFORM_DIR)

    # Bước 2: Lấy API URL từ output
    print("\n[3/4] Lấy API URL từ Terraform output...")
    output_raw = run("terraform output -json", cwd=TERRAFORM_DIR, capture=True)
    outputs = json.loads(output_raw)
    api_url = outputs.get("api_documents_url", {}).get("value", "")
    frontend_url = outputs.get("frontend_url", {}).get("value", "")

    if not api_url:
        sys.exit("❌ Không lấy được api_documents_url từ Terraform output")

    print(f"   API URL: {api_url}")

    # Bước 3: Inject API URL vào frontend/index.html qua meta tag
    with open(FRONTEND_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # Thêm hoặc cập nhật meta tag api-url
    meta_tag = f'<meta name="api-url" content="{api_url}">'
    if '<meta name="api-url"' in html:
        html = re.sub(r'<meta name="api-url"[^>]*>', meta_tag, html)
    else:
        html = html.replace("<head>", f"<head>\n  {meta_tag}", 1)

    with open(FRONTEND_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"   Đã inject API URL vào frontend/index.html")

    # Bước 4: Upload frontend lên S3
    print("\n[4/4] Upload frontend lên S3...")
    run(
        f'aws --endpoint-url={AWS_ENDPOINT} s3 cp '
        f'"{FRONTEND_FILE}" s3://{BUCKET_NAME}/frontend/index.html '
        f'--content-type text/html'
    )

    cloudfront_domain = outputs.get("cloudfront_domain", {}).get("value", "")

    print("\n" + "=" * 60)
    print("✅ Deploy thành công!")
    print(f"\n🌐 Website:    {frontend_url}")
    print(f"📡 API:        {api_url}")
    if cloudfront_domain:
        print(f"☁  CloudFront: https://{cloudfront_domain}/frontend/index.html")
    print("=" * 60)


if __name__ == "__main__":
    main()
