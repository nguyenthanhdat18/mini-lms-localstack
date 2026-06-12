# Mini LMS Cloud — Hệ thống Quản lý Tài liệu Học tập

> **Chủ đề 2:** Nền tảng Quản lý và Chia sẻ Tài nguyên Đa phương tiện  
> Kiến trúc Serverless hoàn toàn trên LocalStack · Tự động hóa 100% bằng Terraform

---

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Luồng dữ liệu chi tiết](#3-luồng-dữ-liệu-chi-tiết)
4. [Dịch vụ tự tìm hiểu](#4-dịch-vụ-tự-tìm-hiểu)
5. [Bảo mật IAM — Nguyên tắc Least Privilege](#5-bảo-mật-iam--nguyên-tắc-least-privilege)
6. [Cấu trúc thư mục](#6-cấu-trúc-thư-mục)
7. [Cài đặt & Chạy dự án](#7-cài-đặt--chạy-dự-án)
8. [Xử lý lỗi & Exception Handling](#8-xử-lý-lỗi--exception-handling)
9. [Kết quả đạt được](#9-kết-quả-đạt-được)
10. [Hạn chế & Hướng phát triển](#10-hạn-chế--hướng-phát-triển)

---

## 1. Giới thiệu

**Mini LMS Cloud** là hệ thống quản lý và chia sẻ tài liệu học tập xây dựng theo mô hình **Serverless** trên nền tảng AWS (giả lập bằng LocalStack). Hệ thống cho phép:

- Upload tài liệu học tập (PDF, DOCX, TXT, ảnh, video)
- Tự động xử lý ảnh: thêm watermark + nén dung lượng ngay khi upload
- Xem danh sách, tìm kiếm, lọc, tải xuống và xóa tài liệu
- Toàn bộ hạ tầng được tự động tạo bằng Terraform, không cần can thiệp thủ công

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        Người dùng (Browser)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  S3 Static Website (Frontend)                    │
│              frontend/index.html — HTML/CSS/JS                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │  REST API calls
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API Gateway (REST API)                      │
│  GET  /documents      → Lambda list-documents                    │
│  POST /documents      → Lambda upload-document                   │
│  DELETE /documents/{id} → Lambda delete-document                 │
└──────┬───────────────────┬──────────────────────┬───────────────┘
       │                   │                      │
       ▼                   ▼                      ▼
┌────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  Lambda    │  │     Lambda       │  │      Lambda         │
│  list-doc  │  │  upload-document │  │  delete-document    │
└─────┬──────┘  └──────┬─────┬────┘  └──────┬──────────────┘
      │                │     │              │
      │ Scan           │ Put │ Put          │ Delete
      ▼                ▼     ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────────────────────┐
│ DynamoDB  │  │ DynamoDB  │  │   S3 Bucket               │
│ Documents │  │ Documents │  │   mini-lms-documents       │
└───────────┘  └───────────┘  │   ├── <file_name>         │
                               │   └── processed/          │
                               │       └── *_watermarked   │
                               └──────────────┬────────────┘
                                              │ S3 ObjectCreated
                                              │ Event Notification
                                              ▼
                                  ┌─────────────────────┐
                                  │      Lambda         │
                                  │  process-document   │
                                  │  (Pillow watermark) │
                                  └──────────┬──────────┘
                                             │ UpdateItem
                                             ▼
                                  ┌──────────────────┐
                                  │    DynamoDB      │
                                  │  status=processed│
                                  └──────────────────┘
```

### Các thành phần chính

| Dịch vụ | Vai trò |
|---|---|
| **S3** | Lưu file vật lý (ảnh, PDF, DOCX...) + host frontend static website |
| **DynamoDB** | Lưu metadata tài liệu (tên, môn học, trạng thái xử lý...) |
| **Lambda** (4 hàm) | Xử lý toàn bộ logic nghiệp vụ không cần server |
| **API Gateway** | Cung cấp REST API cho frontend gọi vào Lambda |
| **S3 Event Notification** | Tự động trigger Lambda khi có file mới upload |
| **IAM Role + Policy** | Kiểm soát quyền truy cập theo nguyên tắc Least Privilege |
| **CloudWatch Logs** | Ghi log runtime của Lambda để debug |

---

## 3. Luồng dữ liệu chi tiết

### 3.1 Luồng Upload tài liệu

```
Người dùng nhập form → JS validate client-side (định dạng, kích thước)
→ FileReader đọc file thành Base64
→ POST /documents với JSON payload
→ API Gateway chuyển tiếp tới Lambda upload-document
→ Lambda validate lại server-side
→ Lambda ghi metadata vào DynamoDB (status = "uploaded")
   [Lý do ghi trước: S3 Event có thể kích hoạt rất nhanh,
    nếu chưa có metadata thì process-document sẽ không tìm thấy document]
→ Lambda upload file lên S3
→ S3 ObjectCreated Event kích hoạt Lambda process-document
→ process-document kiểm tra loại file:
     Nếu là ảnh (PNG/JPG/JPEG):
       - Tải ảnh từ S3 bằng Pillow
       - Thêm watermark "Mini LMS Cloud"
       - Nén chất lượng JPEG = 65%, optimize = True
       - Lưu file mới vào processed/<name>_watermarked.jpg
       - Cập nhật DynamoDB: status="processed", processed_key=..., processed_time=...
     Nếu không phải ảnh:
       - Chỉ cập nhật status="processed"
→ Frontend gọi lại GET /documents để hiển thị cập nhật
```

### 3.2 Luồng Xóa tài liệu

```
Người dùng nhấn nút Xóa
→ Modal xác nhận hiện ra (tránh xóa nhầm)
→ Người dùng xác nhận
→ DELETE /documents/{document_id}
→ API Gateway chuyển tiếp tới Lambda delete-document
→ Lambda tra cứu metadata trong DynamoDB để lấy s3_key và processed_key
→ Lambda xóa file gốc trên S3
→ Lambda xóa file processed (nếu có) trên S3
→ Lambda xóa bản ghi trong DynamoDB
→ Frontend tải lại danh sách
```

### 3.3 Tại sao dùng S3 Event thay vì gọi thẳng?

Giải pháp **Event-Driven** có nhiều ưu điểm:
- **Tách biệt trách nhiệm**: Lambda upload chỉ lo việc upload, không cần biết cách xử lý ảnh
- **Mở rộng dễ dàng**: Có thể thêm nhiều Lambda subscriber (gửi email, tạo thumbnail...) mà không sửa upload
- **Retry tự động**: S3 Event có cơ chế retry nếu Lambda bị lỗi
- **Không block request**: Người dùng không phải chờ xử lý ảnh xong mới nhận response

---

## 4. Dịch vụ tự tìm hiểu

### 4.1 S3 Event Notifications

**Khái niệm**: Khi có file mới được tạo trong S3 (ObjectCreated), S3 tự động gửi một "thông báo" tới dịch vụ khác — trong dự án này là Lambda.

**Cơ chế hoạt động**:
```
File upload → S3 nhận file
           → S3 phát hiện có cấu hình Event Notification
           → S3 tạo event payload dạng JSON:
             {
               "Records": [{
                 "s3": {
                   "bucket": { "name": "mini-lms-documents" },
                   "object": { "key": "banh_flan.png", "size": 317971 }
                 }
               }]
             }
           → S3 gọi Lambda process-document với payload trên
           → Lambda xử lý file
```

**Cấu hình trong Terraform**:
```hcl
resource "aws_s3_bucket_notification" "documents_notification" {
  bucket = var.bucket_name
  lambda_function {
    lambda_function_arn = aws_lambda_function.process_document.arn
    events              = ["s3:ObjectCreated:*"]
  }
}
```

**Lưu ý quan trọng**: Lambda process-document phải bỏ qua các file trong thư mục `processed/` để tránh **vòng lặp vô hạn** (file mới → event → Lambda tạo file processed → event → Lambda tạo file processed → ...).

### 4.2 Pillow — Xử lý ảnh trong Lambda

**Khái niệm**: Pillow là thư viện Python xử lý ảnh phổ biến, cho phép đọc/ghi/chỉnh sửa ảnh trực tiếp trong bộ nhớ (in-memory) mà không cần lưu ra đĩa.

**Chuỗi xử lý ảnh**:
```python
# 1. Tải ảnh từ S3 vào bộ nhớ
image_bytes = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
image = Image.open(BytesIO(image_bytes)).convert("RGB")

# 2. Vẽ watermark lên ảnh
draw = ImageDraw.Draw(image)
draw.text((x, y), "Mini LMS Cloud", fill=(255,255,255), font=font)

# 3. Nén và xuất ra buffer bộ nhớ
buffer = BytesIO()
image.save(buffer, format="JPEG", quality=65, optimize=True)

# 4. Upload file đã xử lý lên S3
s3.put_object(Bucket=bucket, Key=processed_key, Body=buffer.getvalue())
```

**Kết quả**: Ảnh gốc ~310 KB → Ảnh đã xử lý ~22 KB (nén ~93%).

---

## 5. Bảo mật IAM — Nguyên tắc Least Privilege

Nguyên tắc **Least Privilege** (Đặc quyền tối thiểu) yêu cầu mỗi thực thể chỉ được cấp **đúng và đủ** quyền cần thiết để thực hiện nhiệm vụ, không được cấp thừa.

Trong dự án, IAM Policy được chia theo nhóm hành động:

```hcl
# Chỉ cho phép ghi log (không cho xem log của Lambda khác)
"logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"

# Chỉ đọc DynamoDB (Lambda list-documents không cần ghi)
"dynamodb:Scan", "dynamodb:GetItem", "dynamodb:Query"

# Ghi/xóa DynamoDB (Lambda upload/delete mới cần)
"dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem"

# S3 chỉ trong bucket của project (không cho truy cập bucket khác)
Resource: ["arn:aws:s3:::mini-lms-documents",
           "arn:aws:s3:::mini-lms-documents/*"]
```

**So với cách không tốt** (cấp quyền quá rộng):
```json
// KHÔNG NÊN — cho phép Lambda làm bất cứ gì
"Action": "*",
"Resource": "*"
```

---

## 6. Cấu trúc thư mục

```
mini-lms-localstack/
├── deploy.py                    ← Script tự động deploy 1 lệnh
│
├── frontend/
│   └── index.html               ← Giao diện web (API URL tự động inject)
│
├── lambda/
│   ├── list_documents.py        ← Lấy danh sách tài liệu từ DynamoDB
│   ├── upload_document.py       ← Upload file + ghi metadata
│   ├── process_document.py      ← Watermark + nén ảnh (Pillow)
│   ├── delete_document.py       ← Xóa tài liệu (S3 + DynamoDB)
│   └── *.zip                    ← Package Lambda cho Terraform
│
├── terraform/
│   ├── main.tf                  ← Root module: gọi 3 modules con
│   ├── variables.tf             ← Khai báo biến cấu hình
│   ├── outputs.tf               ← Export API URL, bucket name...
│   │
│   └── modules/
│       ├── storage/             ← Module 1: S3 + DynamoDB
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       ├── lambda/              ← Module 2: IAM + 4 Lambda functions
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       │
│       └── api_gateway/         ← Module 3: REST API + CORS + routes
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
│
├── .gitignore
└── README.md
```

### Ý nghĩa của Terraform Modules

| Module | Tài nguyên tạo | Lý do tách riêng |
|---|---|---|
| `storage` | S3 Bucket, DynamoDB Table, S3 CORS | Tái sử dụng: có thể thay bucket name qua variable |
| `lambda` | IAM Role, IAM Policy, 4 Lambda Functions, S3 Notification | Tách bảo mật riêng: IAM Policy chỉ ở đây |
| `api_gateway` | REST API, 3 Resources, 6 Methods, Deployment, Stage | Có thể thêm route mới không ảnh hưởng Lambda/Storage |

---

## 7. Cài đặt & Chạy dự án

### Yêu cầu phần mềm

| Phần mềm | Phiên bản | Lệnh kiểm tra |
|---|---|---|
| Docker Desktop | ≥ 4.0 | `docker --version` |
| Terraform | ≥ 1.5 | `terraform --version` |
| AWS CLI | ≥ 2.0 | `aws --version` |
| Python | ≥ 3.8 | `python --version` |

### Cách 1: Deploy tự động (khuyến nghị)

```powershell
# Bước 1: Clone dự án
git clone https://github.com/nguyenthanhdat18/mini-lms-localstack.git
cd mini-lms-localstack

# Bước 2: Mở Docker Desktop và chạy LocalStack
docker run -d --name mini-lms-localstack -p 4566:4566 -p 4510-4559:4510-4559 `
  -v /var/run/docker.sock:/var/run/docker.sock localstack/localstack:3.8

# Bước 3: Đợi LocalStack sẵn sàng (~15 giây), rồi chạy script deploy
python deploy.py
```

Script `deploy.py` sẽ tự động:
1. Chạy `terraform init` + `terraform apply`
2. Lấy API URL từ Terraform output
3. Inject API URL vào `frontend/index.html`
4. Upload frontend lên S3

M�� website:
```powershell
start http://localhost:4566/mini-lms-documents/frontend/index.html
```

### Cách 2: Deploy thủ công từng bước

```powershell
# Bước 1-2: Giống trên (clone + LocalStack)

# Bước 3: Tạo hạ tầng
cd terraform
terraform init
terraform apply -auto-approve

# Bước 4: Xem API URL
terraform output

# Bước 5: Upload frontend (API URL sẽ được hỏi tự động khi mở web)
aws --endpoint-url=http://localhost:4566 s3 cp `
  ..\frontend\index.html s3://mini-lms-documents/frontend/index.html

# Bước 6: Mở website
start http://localhost:4566/mini-lms-documents/frontend/index.html
```

### Hủy hạ tầng

```powershell
cd terraform
terraform destroy -auto-approve
```

### Kiểm tra sau khi deploy

```powershell
# Kiểm tra Lambda đã tạo
aws --endpoint-url=http://localhost:4566 lambda list-functions --query 'Functions[].FunctionName'

# Kiểm tra API Gateway
aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis

# Kiểm tra DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# Kiểm tra S3
aws --endpoint-url=http://localhost:4566 s3 ls s3://mini-lms-documents
```

---

## 8. Xử lý lỗi & Exception Handling

### Frontend (JavaScript)

| Tình huống lỗi | Cách xử lý |
|---|---|
| Thiếu thông tin form | Validate trước khi gửi, hiển thị thông báo đỏ |
| Định dạng file không hỗ trợ | Kiểm tra extension, liệt kê danh sách được phép |
| File quá lớn (>10 MB) | Tính kích thước trước khi upload, thông báo rõ |
| Lỗi kết nối API | Catch fetch error, hiển thị message cụ thể |
| Đang upload | Disable nút, hiển thị spinner, tránh double-click |
| Xóa nhầm | Modal xác nhận bắt buộc trước khi gọi DELETE |

### Lambda (Python)

| Lambda | Lỗi được xử lý |
|---|---|
| `upload-document` | Thiếu field → 400, Base64 lỗi → 400, file quá lớn → 400, lỗi S3/DynamoDB → 500 |
| `list-documents` | Scan lỗi → 500, trả danh sách rỗng nếu không có dữ liệu |
| `process-document` | Bỏ qua file `frontend/` và `processed/` để tránh loop, lỗi PIL → log và tiếp tục |
| `delete-document` | Không tìm thấy ID → 404, lỗi xóa S3 chỉ log (không crash) |

Tất cả Lambda đều bọc trong `try/except` và trả về JSON lỗi với HTTP status code phù hợp.

---

## 9. Kết quả đạt được

```
[✓] Kiến trúc Serverless hoàn chỉnh: S3 + DynamoDB + Lambda + API Gateway
[✓] Terraform tách module: storage / lambda / api_gateway
[✓] IAM Policy Least Privilege: cấp đúng quyền cho từng Lambda
[✓] S3 Event Notification tự động kích hoạt xử lý ảnh
[✓] Pillow watermark + nén ảnh trong Lambda
[✓] 4 Lambda functions: list / upload / process / delete
[✓] API Gateway: GET + POST + DELETE + OPTIONS (CORS)
[✓] Frontend: loading state, validate client-side, lọc, xóa, thống kê
[✓] API URL động: không hardcode, tự inject từ Terraform output
[✓] Script deploy.py: 1 lệnh deploy toàn bộ
[✓] Exception handling đầy đủ cả frontend lẫn backend
[✓] CloudWatch Logs: Lambda ghi log để debug
```

---

## 10. Hạn chế & Hướng phát triển

| Hạn chế hiện tại | Lý do | Hướng xử lý |
|---|---|---|
| CloudFront CDN | LocalStack Community không hỗ trợ | Bổ sung khi deploy AWS thật |
| Upload Base64 qua API | Giới hạn ~6 MB do API Gateway payload limit | Dùng Pre-signed URL cho file lớn |
| Không có xác thực | Scope đồ án, LocalStack | Thêm Cognito hoặc JWT |
| DynamoDB Scan toàn bảng | Dữ liệu nhỏ, local | Thêm Global Secondary Index khi scale |

---

*Tác giả: Nguyễn Thành Đạt · Repository: https://github.com/nguyenthanhdat18/mini-lms-localstack*
