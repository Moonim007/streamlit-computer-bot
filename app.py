import os
import glob
import streamlit as st
from openai import OpenAI

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ร้านค้าอุปกรณ์คอมพิวเตอร์ & ผู้ช่วย RAG",
    page_icon="💻",
    layout="wide"
)

# 2. ปรับแต่ง UI ด้วย Custom CSS (เมนู Sidebar สไตล์ iHAVECPU + การ์ดสินค้า + แชตฝั่ง User ชิดขวา)
st.markdown("""
<style>
/* ตกแต่งปุ่มเมนูใน Sidebar ให้เหมือน List Menu */
[data-testid="stSidebar"] div.stButton > button {
    width: 100% !important;
    text-align: left !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    box-shadow: none !important;
    margin-bottom: 3px !important;
    transition: all 0.15s ease-in-out !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #f3f4f6 !important;
    color: #e11d48 !important;
}

/* ตกแต่งการ์ดสินค้า */
.product-card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease-in-out;
}
.product-card:hover {
    box-shadow: 0 6px 14px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}
.product-title {
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
    margin-top: 10px;
    min-height: 42px;
    line-height: 1.3;
}
.product-specs {
    font-size: 12px;
    color: #6b7280;
    margin: 8px 0;
    line-height: 1.4;
}
.product-price {
    font-size: 17px;
    font-weight: 700;
    color: #e11d48;
    margin-top: 6px;
}

/* กล่องข้อความแชตฝั่ง User ชิดขวาสไตล์ Messenger */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    margin-left: auto !important;
    margin-right: 0 !important;
    width: fit-content !important;
    max-width: 80% !important;
    flex-grow: 0 !important;
    background-color: transparent !important;
    padding: 0 !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
    background-color: #0084ff !important;
    color: white !important;
    padding: 10px 16px !important;
    border-radius: 18px !important;
    display: inline-block !important;
    width: fit-content !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] p {
    color: white !important;
    margin: 0 !important;
    white-space: pre-wrap !important;
}
</style>
""", unsafe_allow_html=True)

# 3. ฐานข้อมูลสินค้า (อ้างอิงตรงกับชุดข้อมูลในโฟลเดอร์ data/ ทั้งหมด)
PRODUCTS = {
    "โน้ตบุ๊ก (Laptops)": [
        {
            "name": "ASUS Zenbook 14 OLED (UX3405)",
            "specs": "Intel Core Ultra 7 155H | 16GB RAM | 1TB SSD | จอ 14 นิ้ว 3K 120Hz OLED",
            "price": 39990,
            "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&q=80"
        },
        {
            "name": "Lenovo Yoga Slim 7i Aura Edition 15",
            "specs": "Intel Core Ultra 7 258V | 32GB RAM | 1TB SSD | NPU AI 47 TOPS | จอ 2.8K PureSight",
            "price": 45990,
            "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80"
        },
        {
            "name": "HP Pavilion Plus 14",
            "specs": "AMD Ryzen 5 7540U | 16GB RAM | 512GB SSD | Radeon 740M | จอ 2.2K IPS",
            "price": 27990,
            "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&q=80"
        },
        {
            "name": "Dell XPS 13 (9340)",
            "specs": "Intel Core Ultra 7 155H | 32GB RAM | 1TB SSD | จอ 13.4 นิ้ว QHD+ Touchscreen",
            "price": 69990,
            "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&q=80"
        },
        {
            "name": "Acer Nitro V 16 (ANV16-41)",
            "specs": "AMD Ryzen 5 8645HS | RTX 4050 6GB (75W) | 16GB DDR5 | จอ 16 นิ้ว 165Hz",
            "price": 29990,
            "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&q=80"
        },
        {
            "name": "ASUS ROG Strix G16 (G614JVR)",
            "specs": "Intel Core i7-14650HX | RTX 4060 8GB (140W) | 16GB DDR5 | จอ 240Hz ROG Nebula",
            "price": 59990,
            "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&q=80"
        },
        {
            "name": "MSI Katana 15 B13VGK",
            "specs": "Intel Core i7-13620H | RTX 4070 8GB (105W) | 16GB DDR5 | จอ 15.6 นิ้ว 144Hz",
            "price": 42990,
            "image": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400&q=80"
        },
        {
            "name": "Lenovo Legion Pro 5i (16, Gen 9)",
            "specs": "Intel Core i7-14700HX | RTX 4070 8GB (140W) | 32GB DDR5 | จอ WQXGA 240Hz",
            "price": 65990,
            "image": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400&q=80"
        }
    ],
    "การ์ดจอ (GPU)": [
        {
            "name": "NVIDIA GeForce RTX 4060 8GB GDDR6",
            "specs": "CUDA 3,072 | TDP 115W | แนะนำ PSU 550W+ | DLSS 3 / Ray Tracing Gen 3",
            "price": 11500,
            "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"
        },
        {
            "name": "NVIDIA GeForce RTX 4070 Super 12GB GDDR6X",
            "specs": "CUDA 7,168 | TDP 220W | แนะนำ PSU 650W - 750W 80+ Gold | เล่นเกม 2K-4K",
            "price": 24900,
            "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"
        },
        {
            "name": "NVIDIA GeForce RTX 4080 Super 16GB GDDR6X",
            "specs": "CUDA 10,240 | TDP 320W | แนะนำ PSU 750W - 850W+ | รองรับงานประมวลผล AI/LLM และ 4K Ultra",
            "price": 41500,
            "image": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400&q=80"
        },
        {
            "name": "AMD Radeon RX 7600 8GB GDDR6",
            "specs": "Stream Processors 2,048 | TDP 165W | แนะนำ PSU 550W+ | คุ้มค่าสูงสุดสำหรับเกม 1080p",
            "price": 9800,
            "image": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400&q=80"
        },
        {
            "name": "AMD Radeon RX 7800 XT 16GB GDDR6",
            "specs": "Stream Processors 3,840 | TDP 263W | แนะนำ PSU 700W - 750W | VRAM 16GB สำหรับเกม 2K สบายๆ",
            "price": 19500,
            "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"
        }
    ],
    "ซีพียู & ฮาร์ดแวร์ (CPU/RAM/SSD)": [
        {
            "name": "Intel Core i5-14400F (Gen 14)",
            "specs": "10 Cores (6P+4E) 16 Threads | Max 4.7 GHz | Socket LGA1700 | แนะนำ PSU 550W+",
            "price": 6890,
            "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?w=400&q=80"
        },
        {
            "name": "Intel Core i7-14700K (Gen 14)",
            "specs": "20 Cores (8P+12E) 28 Threads | Max 5.6 GHz | แนะนำชุดน้ำ 360mm + PSU 750W-850W",
            "price": 14900,
            "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400&q=80"
        },
        {
            "name": "AMD Ryzen 5 7600X",
            "specs": "6 Cores 12 Threads | Base 4.7 GHz up to 5.3 GHz | Socket AM5 (รองรับ DDR5)",
            "price": 7990,
            "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400&q=80"
        },
        {
            "name": "AMD Ryzen 7 7800X3D",
            "specs": "8 Cores 16 Threads | 3D V-Cache ขนาดใหญ่ 96MB | CPU สำหรับเล่นเกมที่ดีที่สุด",
            "price": 15900,
            "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400&q=80"
        },
        {
            "name": "Kingston FURY Beast DDR4 16GB (8x2) 3200MHz",
            "specs": "ความจุ: 16GB DDR4 | Bus 3200MHz | ประกัน Lifetime ตลอดอายุการใช้งาน",
            "price": 1490,
            "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400&q=80"
        },
        {
            "name": "Corsair Vengeance RGB DDR5 32GB (16x2) 6000MHz",
            "specs": "ความจุ: 32GB DDR5 | Bus 6000MHz CL30 | ไฟ RGB | ประกัน Lifetime",
            "price": 4790,
            "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400&q=80"
        },
        {
            "name": "Kingston NV2 1TB M.2 PCIe 4.0 NVMe",
            "specs": "ความเร็ว Read/Write: 3500/2100 MB/s | ประกันศูนย์ 3 ปี",
            "price": 2190,
            "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&q=80"
        },
        {
            "name": "Samsung 990 PRO 2TB M.2 PCIe 4.0 (มี Heatsink)",
            "specs": "ความเร็ว Read/Write: 7450/6900 MB/s | ใส่ PS5 ได้ | ประกัน 5 ปี",
            "price": 6890,
            "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&q=80"
        }
    ],
    "จอภาพ & เกมมิ่งเกียร์ (Monitors & Gear)": [
        {
            "name": "AOC 24G4 (Gaming Monitor 23.8\")",
            "specs": "Fast IPS | Full HD 1080p | 180Hz | 0.5ms | ประกัน 3 ปี On-site (จุดพิกเซล 3 จุดขึ้นไป)",
            "price": 3990,
            "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"
        },
        {
            "name": "LG UltraGear 27GP850-B (27\" 2K)",
            "specs": "Nano IPS | QHD 2560x1440 | 165Hz (OC 180Hz) | 1ms GtG | ประกัน 3 ปี",
            "price": 11900,
            "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"
        },
        {
            "name": "Dell UltraSharp U2724D (27\" Professional)",
            "specs": "IPS Black Contrast 2000:1 | 120Hz | 98% DCI-P3 | เสียเปลี่ยนตัวใหม่ใน 3 ปี",
            "price": 14500,
            "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"
        },
        {
            "name": "Keychron V1 Max Wireless Mechanical Keyboard",
            "specs": "75% Layout | Gateron Jupiter Switch | Hot-swappable | เชื่อมต่อ 2.4GHz / Bluetooth / Type-C",
            "price": 3890,
            "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&q=80"
        },
        {
            "name": "Logitech G Pro X Superlight 2 Wireless",
            "specs": "เซนเซอร์ HERO 2 (32,000 DPI) | น้ำหนักเบาพิเศษ 60 กรัม | แบตเตอรี่ 95 ชม. | Polling Rate 4K",
            "price": 5290,
            "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=400&q=80"
        },
        {
            "name": "HyperX Cloud III Wireless",
            "specs": "ไดรเวอร์ 53mm | แบตเตอรี่สูงสุด 120 ชม. | DTS Spatial Audio | ประกัน 2 ปี",
            "price": 4990,
            "image": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400&q=80"
        }
    ]
}

# 4. ฟังก์ชันโหลด Knowledge Base จากไฟล์จริงในโฟลเดอร์ data/
@st.cache_data
def load_product_knowledge_base():
    knowledge = ""
    data_folder = "data"
    if os.path.exists(data_folder):
        files = glob.glob(os.path.join(data_folder, "*.txt"))
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                filename = os.path.basename(file_path)
                knowledge += f"\n--- เอกสารข้อมูล: {filename} ---\n{file_content}\n"
            except Exception:
                pass
    return knowledge

knowledge_base = load_product_knowledge_base()

SYSTEM_PROMPT = f"""คุณคือพนักงานและผู้เชี่ยวชาญด้านสินค้าคอมพิวเตอร์และอุปกรณ์ไอที
จงตอบคำถามโดยอ้างอิงจากข้อมูลคลังสินค้าด้านล่างนี้เท่านั้น
กฎสำคัญ:
1. หากไม่มีข้อมูลในคลังสินค้า ให้ตอบตรงๆ ว่า "ขออภัยครับ ไม่พบข้อมูลในระบบ" ห้ามคาดเดาหรือสร้างข้อมูลขึ้นเองเด็ดขาด
2. ตอบข้อมูลสเปก ราคา และเงื่อนไขการรับประกันให้ชัดเจนและสุภาพ

[คลังข้อมูลสินค้า]:
{knowledge_base if knowledge_base else "ไม่มีข้อมูลสินค้าในโฟลเดอร์ data/"}
"""

# 5. กำหนด State เริ่มต้น: เปิดเว็บมาให้อยู่หน้า "🤖 แชตบอต RAG" ทันที
if "active_menu" not in st.session_state:
    st.session_state.active_menu = "rag_chat"

# 6. รายการเมนู Sidebar ตามโฟลเดอร์ data/
menu_items = [
    ("🤖 ผู้ช่วยแชตบอต RAG (ถาม-ตอบ)", "rag_chat"),
    ("💻 โน้ตบุ๊ก ", "โน้ตบุ๊ก (Laptops)"),
    ("🎮 การ์ดจอ ", "การ์ดจอ (GPU)"),
    ("⚙️ ซีพียู และ ฮาร์ดแวร์ ", "ซีพียู & ฮาร์ดแวร์ (CPU/RAM/SSD)"),
    ("🖥️ จอภาพ และ เกมมิ่งเกียร์ ", "จอภาพ & เกมมิ่งเกียร์ (Monitors & Gear)"),
    ("🛡️ นโยบายการรับประกัน ", "warranties")
]

st.sidebar.markdown("<h3 style='margin-bottom: 12px; color: #111827;'>🛒 หมวดหมู่สินค้า</h3>", unsafe_allow_html=True)

# แสดงปุ่มเมนูใน Sidebar
for label, key_val in menu_items:
    btn_text = f"{label}   ❯"
    if st.sidebar.button(btn_text, key=f"menu_{key_val}"):
        st.session_state.active_menu = key_val
        st.rerun()

# ==========================================
# 7. ส่วนแสดงผลเนื้อหา (Main Area)
# ==========================================

# โหมด 1: หน้าแชตบอต RAG (Default)
if st.session_state.active_menu == "rag_chat":
    st.title("🤖 ผู้ช่วยตอบคำถามและเช็กราคาสินค้า (RAG)")
    st.caption("ระบบแชตบอตตอบคำถามโดยอิงจากเอกสารข้อมูลสินค้าในโฟลเดอร์ data/")

    if "OPENROUTER_API_KEY" not in st.secrets:
        st.error("❌ ไม่พบ OPENROUTER_API_KEY ใน Streamlit Secrets กรุณาตั้งค่าก่อนใช้งาน")
        st.stop()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"]
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "สวัสดีครับ! สอบถามข้อมูลสเปก ราคา หรือเช็กเงื่อนไขการรับประกันสินค้าคอมพิวเตอร์ได้เลยครับ"}
        ]

    # แสดงประวัติการแชต
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # ตรวจจับข้อความที่ถูกกดส่งมาจากหน้าร้านค้า
    prompt = None
    if "quick_ask" in st.session_state and st.session_state["quick_ask"]:
        prompt = st.session_state["quick_ask"]
        st.session_state["quick_ask"] = None

    user_input = st.chat_input("พิมพ์คำถามเกี่ยวกับสินค้าคอมพิวเตอร์ที่นี่...")
    if user_input:
        prompt = user_input

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("กำลังค้นหาข้อมูลสินค้า..."):
                try:
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    for m in st.session_state.messages:
                        api_messages.append({"role": m["role"], "content": m["content"]})

                    response = client.chat.completions.create(
                        model="openrouter/free",
                        messages=api_messages,
                        temperature=0.2
                    )
                    bot_reply = response.choices[0].message.content
                    st.write(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ API: {e}")

# โหมด 2: หน้านโยบายการรับประกัน (warranties.txt)
elif st.session_state.active_menu == "warranties":
    st.title("🛡️ นโยบายการรับประกันและการเคลมสินค้า")
    warranty_file_path = os.path.join("data", "warranties.txt")
    if os.path.exists(warranty_file_path):
        with open(warranty_file_path, "r", encoding="utf-8") as f:
            warranty_text = f.read()
        st.markdown(warranty_text)
    else:
        st.info("ไม่พบไฟล์ data/warranties.txt")

# โหมด 3: หน้าแคตตาล็อกสินค้า (ดึงข้อมูลจากตัวแปร PRODUCTS ที่ตรงกับ data)
else:
    current_category = st.session_state.active_menu
    items_to_show = PRODUCTS.get(current_category, [])

    st.title(f"📦 แคตตาล็อก: {current_category}")
    search_query = st.text_input("🔍 ค้นหารายการสินค้า...", placeholder="พิมพ์ชื่อรุ่น เช่น ASUS, RTX, Ryzen...")
    if search_query:
        items_to_show = [item for item in items_to_show if search_query.lower() in item["name"].lower()]

    cols_per_row = 4
    for i in range(0, len(items_to_show), cols_per_row):
        row_items = items_to_show[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, item in zip(cols, row_items):
            with col:
                st.markdown(f"""
                <div class="product-card">
                    <img src="{item['image']}" style="width:100%; height:160px; object-fit:cover; border-radius:8px;">
                    <div class="product-title">{item['name']}</div>
                    <div class="product-specs">{item['specs']}</div>
                    <div class="product-price">฿{item['price']:,}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"💬 ถามสเปก {item['name'][:14]}...", key=f"btn_{item['name']}"):
                    st.session_state["quick_ask"] = f"ขอข้อมูลและสเปกอย่างละเอียดของ {item['name']} ราคา {item['price']:,} บาท หน่อยครับ"
                    st.session_state.active_menu = "rag_chat"
                    st.rerun()