# 🦈 SHARKMMO — HỆ SINH THÁI BÁN SẢN PHẨM MMO TỰ ĐỘNG

> **Slogan:** "Hệ sinh thái sản phẩm MMO tự động"  
> **Phiên bản:** 2.0.0 PRO  
> **Thương hiệu:** SHARKMMO

---

## 📖 1. Tổng quan hệ thống

**SHARKMMO** là nền tảng thương mại điện tử chuyên biệt cho sản phẩm số MMO (Tài khoản AI ChatGPT, Claude, Canva Pro, Proxy/VPN, Tài khoản Mạng xã hội, Dịch vụ giải trí số...). Hệ thống tích hợp trực tiếp với kho nguồn **Canboso API** (`https://canboso.com`), vận hành thông qua **Telegram Bot** song song với **Web Admin Dashboard** hiện đại xây dựng trên Next.js 14 và FastAPI.

### ✨ Tính năng cốt lõi:
- 🤖 **Telegram Bot (aiogram 3.x):** Giao diện tiếng Việt 100%, 8 menu chính trực quan, phân trang sản phẩm mượt mà, hỗ trợ tìm kiếm từ khóa, mua hàng tức thời.
- ⚡ **Tích hợp Canboso API chuẩn Swagger 3.0:** Đầy đủ endpoint Products, Balance, Purchase, Orders với cơ chế bảo vệ `Idempotency-Key` chống tạo đơn lặp và xử lý Rate Limit 429 (`Retry-After`).
- 📈 **Hệ thống Kê giá tự động đa tầng (Pricing Engine):** Admin có thể kê giá theo % hoặc tiền cố định toàn shop, theo từng danh mục, hoặc gán giá cố định riêng cho từng sản phẩm. Tự động làm tròn theo bội số cấu hình.
- 💳 **Thanh toán & Nạp tiền thông minh:** Tự động tạo mã VietQR động với mã chuyển khoản riêng biệt, hỗ trợ Webhook SePay/Ngân hàng để cộng tiền tự động 24/7 và có cơ chế duyệt thủ công cho Admin.
- 💼 **Bảng điều khiển Quản trị (Admin Panel Next.js):** Dark mode công nghệ theo phong cách Shark Mascot, hiển thị biểu đồ doanh thu/lợi nhuận, quản lý đơn hàng kèm chi tiết tài khoản đã bàn giao, quản lý người dùng và số dư kho Canboso.

---

## 🏗️ 2. Kiến trúc thư mục dự án

```
sharkmmo/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI REST API
│   │   │   ├── deps.py          # Dependency injection & Auth checks
│   │   │   ├── router.py        # Master router
│   │   │   └── v1/              # Endpoints: dashboard, products, pricing, orders, users, payments, webhooks, settings
│   │   ├── bot/                 # Aiogram 3.x Telegram Bot setup
│   │   │   ├── bot.py           # Bot instance & Dispatcher configuration
│   │   │   └── middlewares/     # DbSession, UserAuth (tự tạo tài khoản), Throttling (chống spam)
│   │   ├── core/                # Cấu hình Pydantic Settings & biến môi trường
│   │   │   └── config.py
│   │   ├── database/            # SQLAlchemy 2.0 Async Session
│   │   │   └── session.py
│   │   ├── handlers/            # Bộ xử lý lệnh & sự kiện Telegram Bot
│   │   │   ├── start.py         # Lệnh /start & banner chào mừng
│   │   │   ├── catalog.py       # Danh mục, phân trang sản phẩm
│   │   │   ├── search.py        # Tìm kiếm sản phẩm theo tên/từ khóa
│   │   │   ├── wallet.py        # Ví cá nhân & nạp tiền VietQR
│   │   │   ├── orders.py        # Xem lịch sử đơn hàng & thông tin tài khoản
│   │   │   ├── promotions.py    # Ưu đãi sỉ & khuyến mãi
│   │   │   ├── account.py       # Hồ sơ & phân hạng thành viên
│   │   │   ├── support.py       # Trung tâm hỗ trợ & bảo hành
│   │   │   ├── buy_flow.py      # Quy trình mua hàng FSM (số lượng, email, slot...)
│   │   │   └── admin_bot.py     # Lệnh quản trị nhanh trong bot (/admin, /balance, /sync)
│   │   ├── keyboards/           # ReplyKeyboardMarkup & InlineKeyboardMarkup
│   │   │   └── menus.py
│   │   ├── models/              # Database models: User, ProductCache, PricingRule, Order, PaymentTransaction, Setting, AdminLog
│   │   │   └── models.py
│   │   ├── payments/            # Xử lý thanh toán VietQR & SePay Webhook
│   │   │   ├── vietqr.py        # Tạo link ảnh VietQR QuickLink chuẩn
│   │   │   ├── payment_service.py # Xử lý giao dịch nạp tiền & duyệt tiền
│   │   │   └── sepay.py         # Nhận & đối soát Webhook SePay tự động
│   │   ├── services/            # Nghiệp vụ lõi
│   │   │   ├── canboso.py       # Canboso API Client (OpenAPI 3.0.3)
│   │   │   ├── pricing.py       # Pricing Engine kê giá tự động
│   │   │   ├── product_sync.py  # Đồng bộ danh mục từ Canboso vào Database
│   │   │   └── order_service.py # Quản lý đơn hàng, lock mua hàng, gọi Canboso purchase
│   │   └── utils/
│   ├── tests/                   # Kiểm thử tự động pytest
│   │   ├── test_canboso_client.py
│   │   ├── test_pricing.py
│   │   ├── test_order_service.py
│   │   └── test_payments.py
│   ├── Dockerfile
│   ├── main.py                  # Điểm khởi chạy backend (FastAPI + Bot Polling + Sync Scheduler)
│   └── requirements.txt
├── dashboard/                   # Next.js 14 + Tailwind CSS + Lucide Icons Admin Dashboard
│   ├── app/
│   │   ├── globals.css          # Theme SHARKMMO Dark mode
│   │   ├── layout.tsx
│   │   └── page.tsx             # Master Admin Hub
│   ├── components/
│   │   ├── Sidebar.tsx          # Menu điều hướng chính
│   │   ├── Navbar.tsx           # Thanh header với cảnh báo số dư kho Canboso
│   │   ├── DashboardView.tsx    # Biểu đồ doanh thu/lợi nhuận & thẻ thống kê
│   │   ├── ProductsView.tsx     # Bảng sản phẩm & modal chỉnh sửa giá
│   │   ├── PricingRulesView.tsx # Quản lý quy tắc kê giá toàn hệ thống / danh mục
│   │   ├── OrdersView.tsx       # Bảng đơn hàng & xem chi tiết bàn giao tài khoản
│   │   ├── UsersView.tsx        # Quản lý khách hàng, số dư ví & khóa tài khoản
│   │   ├── PaymentsView.tsx     # Bảng nạp tiền VietQR & 1-click duyệt nạp
│   │   └── SettingsView.tsx     # Cấu hình tài khoản ngân hàng & Webhook
│   ├── lib/
│   │   ├── api.ts               # REST API Client kết nối Backend
│   │   └── utils.ts
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docker-compose.yml           # Triển khai trọn bộ Backend + Dashboard với 1 lệnh
├── .env.example                 # Mẫu cấu hình môi trường chuẩn
├── pytest.ini                   # Cấu hình test runner
└── README.md
```

---

## 🔌 3. Tích hợp Canboso API (Swagger Analysis)

Theo tài liệu chính thức OpenAPI 3.0.3 tại `https://canboso.com/api/swagger/`:

### Phương thức xác thực:
- Header: `x-buyer-key: <CANBOSO_API_KEY>` (Định dạng khóa `tgb_...`).
- Query Param (dự phòng): `?key=<CANBOSO_API_KEY>`.

### Các Endpoint được tích hợp:
1. **Lấy danh sách sản phẩm:** `GET /api/v2/telegram-buyer/products`
   - Quota: 30 requests / 60 giây.
   - Response: Danh sách sản phẩm gồm `productId`, `name`, `productType` (account, slot, upgrade_account), `price`, `availability`, `promotions`, `purchaseRequirements`.
   - Cơ chế Cache: SHARKMMO lưu cache bộ nhớ trong 60s để tránh vượt rate limit.
2. **Kiểm tra số dư kho nguồn:** `GET /api/v2/telegram-buyer/balance`
   - Quota: 30 requests / 60 giây.
   - Response: `balance` (VND), `usdtBalance` (USDT), `walletCurrency`.
   - Cảnh báo: Tự động phát cảnh báo khi số dư nguồn thấp hơn ngưỡng quy định.
3. **Thực hiện mua hàng:** `POST /api/v2/telegram-buyer/purchase`
   - Bắt buộc Header: `Idempotency-Key` (chuỗi duy nhất từ 8 đến 128 ký tự).
   - Payload:
     ```json
     {
       "key": "tgb_...",
       "product_id": "64f0c0f2b9...",
       "quantity": 1,
       "customer_email": "buyer@example.com",
       "slot_months": 3
     }
     ```
   - Xử lý kết quả: Trích xuất danh sách tài khoản được cấp trong `delivery.accounts` (`user`, `password`, `verifyEmail`, `expiryText`, `otherInfo`) để bàn giao cho khách.
4. **Lịch sử đơn nguồn:** `GET /api/v2/telegram-buyer/orders?orderCode=...`

### Quy định xử lý Rate Limit (HTTP 429):
Canboso áp dụng hình phạt tăng dần (1 phút, 5 phút, 15 phút, 1 giờ, 6 giờ). Backend SHARKMMO tự động đọc header `Retry-After` và tạm hoãn gọi API, tuyệt đối không gửi request dồn dập (tight loop).

---

## 📈 4. Hệ thống Kê giá tự động (Pricing Engine)

Cơ chế tính giá bán theo thứ tự ưu tiên:
1. **Ưu tiên 1 (Sản phẩm riêng lẻ):** Admin có thể nhập giá bán trực tiếp (Override Price) hoặc % markup riêng cho sản phẩm đó.
2. **Ưu tiên 2 (Theo danh mục):** Áp dụng quy tắc cộng lãi riêng theo từng danh mục (Ví dụ: `🤖 AI & Đồ họa` +15%, `🛡️ Proxy & VPN` +30%).
3. **Ưu tiên 3 (Toàn hệ thống - Global):** Áp dụng tỷ lệ markup toàn shop (Ví dụ: +20% hoặc +10.000đ).
4. **Tự động làm tròn:** Mọi mức giá sau khi tính toán sẽ được làm tròn lên theo bước nhảy cấu hình (mặc định 1.000 VND).
5. **Bảo toàn lợi nhuận:** Khi Canboso API cập nhật giá nguồn mới, giá bán tại SHARKMMO sẽ tự động tính toán lại mà không làm mất tỷ lệ % lãi đã đặt.

---

## 💳 5. Hệ thống Thanh toán VietQR & SePay Webhook

### Quy trình nạp tiền & mua hàng:
1. Khách hàng chọn **💰 Ví của tôi** hoặc nhấn mua khi số dư chưa đủ.
2. Bot tạo mã giao dịch nạp tiền độc nhất (Ví dụ: `NAP261102A1B2C3`) và hiển thị ảnh **VietQR QuickLink** có sẵn số tiền và nội dung chuyển khoản:
   `SHARK NAP <TELEGRAM_ID> <MÃ_GIAO_DỊCH>`
3. Khách quét mã QR và xác nhận thanh toán qua App ngân hàng.
4. Hệ thống ngân hàng/SePay gửi thông báo qua Webhook `POST /api/v1/webhooks/sepay`.
5. Backend xác thực chữ ký token, kiểm tra chống webhook trùng lặp (`gateway_tx_id`), đối soát đúng số tiền và tự động cộng số dư vào ví khách hàng trong vòng 10-30 giây.
6. Trường hợp cần duyệt tay, Admin có thể truy cập Web Dashboard hoặc gõ `/admin` trong bot để bấm **✅ Duyệt nạp tiền** với 1 chạm.

---

## 🚀 6. Hướng dẫn cài đặt & Khởi chạy

### Cách 1: Triển khai nhanh bằng Docker Compose (Khuyên dùng cho VPS)

1. **Clone mã nguồn về máy chủ:**
   ```bash
   git clone <repo_url>
   cd sharkmmo
   ```

2. **Cấu hình file môi trường `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Điền `BOT_TOKEN` từ @BotFather và `CANBOSO_API_KEY` từ Canboso.*

3. **Khởi chạy toàn bộ hệ thống:**
   ```bash
   docker compose up -d --build
   ```

4. **Truy cập:**
   - **Telegram Bot:** Tìm username bot của bạn trên Telegram và gõ `/start`.
   - **Web Admin Dashboard:** `http://<IP_VPS>:3000`
   - **Backend API & Swagger Docs:** `http://<IP_VPS>:8000/docs`

---

### Cách 2: Chạy trực tiếp trên môi trường Local (Windows / Linux)

#### Yêu cầu:
- Python 3.12+
- Node.js 20+

#### Bước 1: Khởi chạy Backend (FastAPI + Telegram Bot)
```bash
# Cài đặt thư viện Python
pip install -r backend/requirements.txt

# Khởi chạy Backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Ghi chú: Khi Backend khởi chạy, nó sẽ tự động kết nối và chạy Telegram Bot Polling trong luồng nền.*

#### Bước 2: Khởi chạy Web Dashboard
```bash
cd dashboard
npm install
npm run dev
```
*Dashboard sẽ chạy tại `http://localhost:3000`.*

---

## 🧪 7. Chạy kiểm thử tự động (Unit & Integration Tests)

Dự án có sẵn bộ test tự động kiểm thử toàn diện Canboso Client, Pricing Engine, Order Engine và Payment Webhook:

```bash
pytest backend/tests -v
```

Kết quả mong đợi:
```
backend/tests/test_canboso_client.py::test_headers_and_idempotency PASSED
backend/tests/test_canboso_client.py::test_get_balance_success PASSED
backend/tests/test_canboso_client.py::test_rate_limit_error_retry_after PASSED
backend/tests/test_canboso_client.py::test_auth_error_handling PASSED
backend/tests/test_canboso_client.py::test_purchase_success PASSED
backend/tests/test_order_service.py::test_order_insufficient_balance PASSED
backend/tests/test_order_service.py::test_order_purchase_success PASSED
backend/tests/test_payments.py::test_vietqr_url_generation PASSED
backend/tests/test_payments.py::test_deposit_and_manual_confirmation PASSED
backend/tests/test_payments.py::test_sepay_webhook_auto_match PASSED
backend/tests/test_pricing.py::test_global_pricing_rule PASSED
backend/tests/test_pricing.py::test_category_pricing_override PASSED
backend/tests/test_pricing.py::test_product_direct_override PASSED
backend/tests/test_pricing.py::test_rounding_mechanism PASSED
============================== 14 passed ==============================
```

---

## 🛡️ 8. Bảo mật & Tiêu chuẩn vận hành

1. **Bảo vệ khóa bí mật:** `BOT_TOKEN` và `CANBOSO_API_KEY` luôn được lưu trong `.env` và được che mã trong giao diện Dashboard.
2. **Chống tạo đơn trùng (Idempotency):** Mọi giao dịch đặt hàng đều tạo `idempotency_key` duy nhất và sử dụng asyncio user lock để chặn hành vi nhấp nút liên tục từ người dùng.
3. **Đối soát giao dịch:** Số dư kho nguồn Canboso và số dư ví khách hàng được hạch toán tách biệt 100%. Nếu đơn hàng thất bại từ nhà cung cấp, hệ thống tự động hoàn tiền lại ví khách và ghi nhận nhật ký lỗi.
4. **Chống giả mạo thanh toán:** Khớp đúng số tiền và nội dung mã nạp tiền, bảo vệ bằng mã hóa chữ ký Webhook token.

---

## 📞 Hỗ trợ & Bản quyền

- **Thương hiệu:** SHARKMMO
- **Đội ngũ phát triển:** SHARKMMO Engineering Team
- **Hỗ trợ kỹ thuật:** Telegram @SharkMMO_Support
