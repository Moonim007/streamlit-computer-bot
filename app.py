import os
import glob
import re
import streamlit as st
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# ==========================================
# 1. การตั้งค่าหน้าเว็บ (Page Config)
# ==========================================
st.set_page_config(
    page_title="ร้านค้าอุปกรณ์คอมพิวเตอร์ & ผู้ช่วย RAG",
    page_icon="💻",
    layout="wide"
)

# ==========================================
# 2. ปรับแต่ง UI ด้วย Custom CSS
# ==========================================
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

/* ตกแต่งการ์ดสินค้า E-commerce */
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

/* ตกแต่งกล่องข้อความฝั่ง User ให้ชิดขวาแบบ Messenger */
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

# ==========================================
# 3. ข้อมูลสินค้าสำหรับแสดงแคตตาล็อกหน้าร้าน
# ==========================================
PRODUCTS = {
    "โน้ตบุ๊ก (Laptops)": [
        {"name": "ASUS Zenbook 14 OLED (UX3405)", "specs": "Intel Core Ultra 7 155H | 16GB RAM | 1TB SSD | จอ 14 นิ้ว 3K OLED 120Hz", "price": 39990, "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400&q=80"},
        {"name": "Lenovo Yoga Slim 7i Aura Edition 15", "specs": "Intel Core Ultra 7 258V | 32GB RAM | 1TB SSD | NPU AI 47 TOPS | จอ 2.8K PureSight Touch", "price": 45990, "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80"},
        {"name": "HP Pavilion Plus 14", "specs": "AMD Ryzen 5 7540U | 16GB RAM | 512GB SSD | จอ 2.2K IPS 100% sRGB", "price": 27990, "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&q=80"},
        {"name": "Dell XPS 13 (9340)", "specs": "Intel Core Ultra 7 155H | 32GB RAM | 1TB SSD | จอ 13.4 นิ้ว QHD+ Touchscreen", "price": 69990, "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&q=80"},
        {"name": "Acer Nitro V 16 (ANV16-41)", "specs": "AMD Ryzen 5 8645HS | RTX 4050 6GB (75W) | 16GB DDR5 | จอ 165Hz", "price": 29990, "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&q=80"},
        {"name": "ASUS ROG Strix G16 (G614JVR)", "specs": "Intel Core i7-14650HX | RTX 4060 8GB (140W) | 16GB DDR5 | จอ 240Hz ROG Nebula", "price": 59990, "image": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400&q=80"},
        {"name": "MSI Katana 15 B13VGK", "specs": "Intel Core i7-13620H | RTX 4070 8GB (105W) | 16GB DDR5 | จอ 15.6 นิ้ว 144Hz", "price": 42990, "image": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400&q=80"},
        {"name": "Lenovo Legion Pro 5i (16, Gen 9)", "specs": "Intel Core i7-14700HX | RTX 4070 8GB (140W) | 32GB DDR5 | จอ WQXGA 240Hz", "price": 65990, "image": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400&q=80"}
    ],
    "การ์ดจอ (GPU)": [
        {"name": "NVIDIA GeForce RTX 4060 8GB GDDR6", "specs": "CUDA 3,072 | TDP 115W | แนะนำ PSU 550W+ | เล่นเกม 1080p Ultra ลื่นไหล", "price": 11500, "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"},
        {"name": "NVIDIA GeForce RTX 4070 Super 12GB GDDR6X", "specs": "CUDA 7,168 | TDP 220W | แนะนำ PSU 650W - 750W 80+ Gold | เล่นเกม 2K-4K ปรับสุด", "price": 24900, "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"},
        {"name": "NVIDIA GeForce RTX 4080 Super 16GB GDDR6X", "specs": "CUDA 10,240 | TDP 320W | แนะนำ PSU 750W - 850W+ | เหมาะสำหรับเกม 4K Ultra และงาน AI/3D", "price": 41500, "image": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400&q=80"},
        {"name": "AMD Radeon RX 7600 8GB GDDR6", "specs": "Stream Processors 2,048 | TDP 165W | แนะนำ PSU 550W+ | คุ้มค่าสำหรับการเล่นเกม 1080p", "price": 9800, "image": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400&q=80"},
        {"name": "AMD Radeon RX 7800 XT 16GB GDDR6", "specs": "Stream Processors 3,840 | TDP 263W | แนะนำ PSU 700W - 750W | VRAM 16GB สำหรับเกม 2K สบายๆ", "price": 19500, "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400&q=80"}
    ],
    "ซีพียู & ฮาร์ดแวร์ (CPU/RAM/SSD)": [
        {"name": "Intel Core i5-14400F (Gen 14)", "specs": "10 Cores (6P+4E) 16 Threads | Max 4.7 GHz | Socket LGA1700 | แนะนำ PSU 550W+", "price": 6890, "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?w=400&q=80"},
        {"name": "Intel Core i7-14700K (Gen 14)", "specs": "20 Cores (8P+12E) 28 Threads | Max 5.6 GHz | แนะนำชุดน้ำ 360mm + PSU 750W-850W", "price": 14900, "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=400&q=80"},
        {"name": "AMD Ryzen 5 7600X", "specs": "6 Cores 12 Threads | Base 4.7 GHz up to 5.3 GHz | Socket AM5 (รองรับ DDR5)", "price": 7990, "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400&q=80"},
        {"name": "AMD Ryzen 7 7800X3D", "specs": "8 Cores 16 Threads | 3D V-Cache 96MB | CPU สำหรับเล่นเกมที่ดีที่สุด", "price": 15900, "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400&q=80"},
        {"name": "Kingston FURY Beast DDR4 16GB (8x2) 3200MHz", "specs": "16GB DDR4 | Bus 3200MHz | ประกันตลอดอายุการใช้งาน Lifetime", "price": 1490, "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400&q=80"},
        {"name": "Corsair Vengeance RGB DDR5 32GB (16x2) 6000MHz", "specs": "32GB DDR5 | Bus 6000MHz CL30 | ไฟ RGB | ประกัน Lifetime", "price": 4790, "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400&q=80"},
        {"name": "Kingston NV2 1TB M.2 PCIe 4.0 NVMe", "specs": "Speed Read/Write: 3500/2100 MB/s | ประกัน 3 ปี", "price": 2190, "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&q=80"},
        {"name": "Samsung 990 PRO 2TB M.2 PCIe 4.0 (Heatsink)", "specs": "Speed Read/Write: 7450/6900 MB/s | ใส่ PS5 ได้ | ประกัน 5 ปี", "price": 6890, "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400&q=80"}
    ],
    "จอภาพ & เกมมิ่งเกียร์ (Monitors & Gear)": [
        {"name": "AOC 24G4 (Gaming Monitor 23.8\")", "specs": "Fast IPS | FHD 1080p | 180Hz | 0.5ms | ประกัน 3 ปี On-site (เคลม 3 จุดขึ้นไป)", "price": 3990, "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"},
        {"name": "LG UltraGear 27GP850-B (27\" 2K)", "specs": "Nano IPS | QHD 2560x1440 | 165Hz (OC 180Hz) | 1ms | ประกัน 3 ปี", "price": 11900, "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"},
        {"name": "Dell UltraSharp U2724D (27\" Pro)", "specs": "IPS Black Contrast 2000:1 | 120Hz | 98% DCI-P3 | เสียเปลี่ยนตัวใหม่ใน 3 ปี", "price": 14500, "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&q=80"},
        {"name": "Keychron V1 Max Wireless Mechanical Keyboard", "specs": "75% Layout | Gateron Jupiter | Hot-swappable | 2.4GHz / Bluetooth / Type-C", "price": 3890, "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&q=80"},
        {"name": "Logitech G Pro X Superlight 2 Wireless", "specs": "เซนเซอร์ HERO 2 (32K DPI) | น้ำหนักเบา 60g | แบต 95 ชม. | Polling Rate 4K", "price": 5290, "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=400&q=80"},
        {"name": "HyperX Cloud III Wireless", "specs": "ไดรเวอร์ 53mm | แบตเตอรี่สูงสุด 120 ชม. | DTS Spatial Audio | ประกัน 2 ปี", "price": 4990, "image": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400&q=80"}
    ]
}

# ==========================================
# 4. RAG Core Pipeline (Regex Chunking + Keyword Fallback)
# ==========================================
def load_and_chunk_documents(data_folder="data"):
    """โหลดเอกสารและตัดแบ่ง Chunk ทีละรายการสินค้าอย่างแม่นยำ"""
    documents = []
    sources = []
    file_paths = glob.glob(os.path.join(data_folder, "*.txt"))
    
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # แยกข้อความเมื่อขึ้นต้นด้วยตัวเลขและจุด เช่น 1., 2., 3. หรือหัวข้อหลัก ===
        raw_items = re.split(r'\n(?=[0-9]+\.\s)|\n(?====)', content)
        
        for item in raw_items:
            cleaned = item.strip()
            # ตัดบรรทัดหัวเรื่อง === บนสุดออกถ้ามี เพื่อไม่ให้กวน Vector
            if cleaned.startswith("===") and "\n1." in cleaned:
                cleaned = cleaned.split("\n1.", 1)[-1]
                cleaned = "1." + cleaned
                
            if len(cleaned) > 25:
                documents.append(cleaned)
                sources.append(file_name)

    return documents, sources

@st.cache_resource(show_spinner="กำลังโหลดและสร้าง Vector Index...")
def init_vector_db():
    docs, doc_sources = load_and_chunk_documents()
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    embeddings = model.encode(docs, convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(embeddings)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    return model, index, docs, doc_sources

embed_model, faiss_index, documents, sources = init_vector_db()

def search_context(query, top_k=6):
    """ค้นหาด้วย Cosine Similarity พร้อมดึงรหัสรุ่นสำคัญมาไว้ลำดับแรก"""
    query_vector = embed_model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vector)
    
    distances, indices = faiss_index.search(query_vector, top_k)
    retrieved_docs = []
    retrieved_sources = []
    
    for idx in indices[0]:
        if idx < len(documents):
            retrieved_docs.append(documents[idx])
            retrieved_sources.append(sources[idx])

    # ค้นหารหัสรุ่นเฉพาะ เช่น 4060, 4070, 4080, 7600, 7800, 7800X3D, 14400F, Zenbook
    key_models = re.findall(r'\b(?:RTX\s*)?[0-9]{4}(?:[A-Za-z0-9]+)?\b|[A-Za-z0-9\-]{4,}', query, re.IGNORECASE)
    for model_code in key_models:
        if len(model_code) >= 4 and (not model_code.isdigit() or len(model_code) == 4):
            for doc, src in zip(documents, sources):
                if model_code.lower() in doc.lower() and doc not in retrieved_docs:
                    retrieved_docs.insert(0, doc)
                    retrieved_sources.insert(0, src)
                    break

    return retrieved_docs[:top_k], retrieved_sources[:top_k]

# ==========================================
# 5. Sidebar Navigation
# ==========================================
if "active_menu" not in st.session_state:
    st.session_state.active_menu = "rag_chat"

menu_items = [
    ("🤖 ผู้ช่วยแชตบอต RAG (ถาม-ตอบ)", "rag_chat"),
    ("💻 โน้ตบุ๊ก (laptops.txt)", "โน้ตบุ๊ก (Laptops)"),
    ("🎮 การ์ดจอ (gpu_specs.txt)", "การ์ดจอ (GPU)"),
    ("⚙️ ซีพียู และ ฮาร์ดแวร์ (cpu_specs.txt)", "ซีพียู & ฮาร์ดแวร์ (CPU/RAM/SSD)"),
    ("🖥️ จอภาพ และ เกมมิ่งเกียร์ (monitors.txt)", "จอภาพ & เกมมิ่งเกียร์ (Monitors & Gear)"),
    ("🛡️ นโยบายการรับประกัน (warranties.txt)", "warranties")
]

st.sidebar.markdown("<h3 style='margin-bottom: 12px; color: #111827;'>🛒 หมวดหมู่สินค้า</h3>", unsafe_allow_html=True)
for label, key_val in menu_items:
    btn_text = f"{label}   ❯"
    if st.sidebar.button(btn_text, key=f"menu_{key_val}"):
        st.session_state.active_menu = key_val
        st.rerun()

# ==========================================
# 6. ส่วนแสดงผลเนื้อหา (Main Content)
# ==========================================
if st.session_state.active_menu == "rag_chat":
    st.title("🤖 ผู้ช่วยตอบคำถามและเช็กราคาสินค้า (RAG)")
    st.caption("ระบบแชตบอต RAG ตอบคำถามจากเอกสารข้อมูลสินค้าพร้อมแสดงแหล่งอ้างอิง")

    if "OPENROUTER_API_KEY" not in st.secrets:
        st.error("❌ ไม่พบ OPENROUTER_API_KEY ใน Streamlit Secrets กรุณาตั้งค่าก่อนใช้งาน")
        st.stop()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"]
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "สวัสดีครับ! สอบถามข้อมูลสเปก ราคา หรือเช็กเงื่อนไขการรับประกันสินค้าได้เลยครับ"}
        ]

    # แสดงประวัติการสนทนาพร้อมแหล่งอ้างอิง
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 แหล่งอ้างอิงข้อมูล (Context Source)"):
                    for src, doc in zip(message["sources"], message["docs"]):
                        st.caption(f"**ไฟล์ต้นฉบับ:** {src}")
                        st.text(doc)

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

        # ทำ Vector Search ดึง Chunk ที่เกี่ยวข้อง
        retrieved_docs, retrieved_sources = search_context(prompt, top_k=6)
        context_text = "\n---\n".join(retrieved_docs)

        # Strict RAG Prompt
        system_prompt = f"""คุณคือพนักงานและผู้เชี่ยวชาญด้านสินค้าคอมพิวเตอร์และอุปกรณ์ไอที
จงตอบคำถามโดยอาศัย [บริบทข้อมูลสินค้า (Context)] ที่กำหนดให้เท่านั้น

กฎเหล็กสำคัญ:
1. ต้องตอบคำถามเป็น "ภาษาไทย" เท่านั้น ห้ามใช้ภาษาจีนหรือภาษาอื่น
2. หากไม่มีข้อมูลหรือคำตอบใน Context ให้ตอบว่า "ขออภัยครับ ไม่พบข้อมูลในระบบ" ห้ามคาดเดาหรือสร้างข้อมูลขึ้นเองเด็ดขาด
3. สรุปข้อมูลสเปก ราคา และเงื่อนไขการรับประกันให้กระชับ ชัดเจน และสุภาพ

[บริบทข้อมูลสินค้า (Context)]:
{context_text}
"""

        with st.chat_message("assistant"):
            with st.spinner("กำลังค้นหาข้อมูลสินค้า..."):
                try:
                    user_query = f"จงตอบคำถามต่อไปนี้เป็นภาษาไทยเท่านั้น:\n{prompt}"

                    response = client.chat.completions.create(
                        model="openrouter/free",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_query}
                        ],
                        temperature=0.2
                    )
                    bot_reply = response.choices[0].message.content
                    st.write(bot_reply)

                    # แสดงกล่องแหล่งอ้างอิง
                    with st.expander("📚 แหล่งอ้างอิงข้อมูล (Context Source)"):
                        for src, doc in zip(retrieved_sources, retrieved_docs):
                            st.caption(f"**ไฟล์ต้นฉบับ:** {src}")
                            st.text(doc)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_reply,
                        "sources": retrieved_sources,
                        "docs": retrieved_docs
                    })
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ API: {e}")

elif st.session_state.active_menu == "warranties":
    st.title("🛡️ นโยบายการรับประกันและการเคลมสินค้า")
    warranty_file_path = os.path.join("data", "warranties.txt")
    if os.path.exists(warranty_file_path):
        with open(warranty_file_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("ไม่พบไฟล์ data/warranties.txt")

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
                    st.session_state["quick_ask"] = f"ขอข้อมูลและสเปกอย่างละเอียดของ {item['name']} หน่อยครับ"
                    st.session_state.active_menu = "rag_chat"
                    st.rerun()