import os
import glob
import streamlit as st
from openai import OpenAI

# ----------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ (Streamlit Page Configuration)
# ----------------------------------------------------
st.set_page_config(
    page_title="ผู้ช่วยตอบคำถามและเช็กราคาสินค้าคอมพิวเตอร์",
    page_icon="💻",
    layout="centered"
)

# ----------------------------------------------------
# 2. ตกแต่ง UI ด้วย Custom CSS (จัดฝั่ง User ชิดขวาแบบ Facebook)
# ----------------------------------------------------
st.markdown("""
<style>
/* 1. สลับให้ Avatar ไปอยู่ขวาสุด และจัด Element เรียงขวาไปซ้าย */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
}

/* 2. ดันตัวคอนเทนเนอร์แชตฝั่ง User ทั้งหมดไปขวาสุด และหดขนาดตามเนื้อหา */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    margin-left: auto !important;
    margin-right: 0 !important;
    width: fit-content !important;
    max-width: 80% !important;
    flex-grow: 0 !important;
    background-color: transparent !important;
    padding: 0 !important;
}

/* 3. ตกแต่งกล่องข้อความสีฟ้า */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
    background-color: #0084ff !important;
    color: white !important;
    padding: 10px 16px !important;
    border-radius: 18px !important;
    display: inline-block !important;
    width: fit-content !important;
}

/* 4. จัดตัวหนังสือข้างใน */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] p {
    color: white !important;
    margin: 0 !important;
    white-space: pre-wrap !important;
}
</style>
""", unsafe_allow_html=True)

st.title("💻 ผู้ช่วยตอบคำถามและเช็กราคาสินค้าคอมพิวเตอร์")
st.caption("ระบบแชตบอต RAG ตอบคำถามสเปก ราคา และการใช้งานจากคลังข้อมูลสินค้า")

# ----------------------------------------------------
# 3. ตรวจสอบและดึง API Key จาก .streamlit/secrets.toml
# ----------------------------------------------------
if "OPENROUTER_API_KEY" not in st.secrets:
    st.error("❌ ไม่พบ OPENROUTER_API_KEY ในไฟล์ .streamlit/secrets.toml กรุณาตรวจสอบการตั้งค่า")
    st.stop()

# เชื่อมต่อ OpenRouter ผ่าน OpenAI Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
)

# ----------------------------------------------------
# 4. ฟังก์ชันโหลดข้อมูลสินค้าจากโฟลเดอร์ data/
# ----------------------------------------------------
@st.cache_data
def load_product_knowledge_base():
    knowledge = ""
    data_folder = "data"
    if os.path.exists(data_folder):
        files = glob.glob(os.path.join(data_folder, "*.*"))
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

SYSTEM_PROMPT = f"""คุณคือผู้ช่วยตอบคำถามและเช็กราคาสินค้าคอมพิวเตอร์และอุปกรณ์ไอทีที่เป็นมิตรและเชี่ยวชาญ
จงตอบคำถามโดยอ้างอิงจากข้อมูลคลังสินค้าที่กำหนดให้อย่างถูกต้อง แม่นยำ หากไม่มีข้อมูลในคลังสินค้า ให้แจ้งผู้ใช้ตามตรงอย่างสุภาพ

[คลังข้อมูลสินค้า]:
{knowledge_base if knowledge_base else "ไม่มีข้อมูลสินค้าในโฟลเดอร์ data/"}
"""

# ----------------------------------------------------
# 5. จัดการ Session State สำหรับประวัติการแชต
# ----------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "สวัสดีครับ! สอบถามข้อมูลสเปก ราคา หรือการใช้งานคอมพิวเตอร์และอุปกรณ์ไอทีได้เลยครับ"}
    ]

# แสดงประวัติการสนทนาบน UI
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ----------------------------------------------------
# 6. ส่วนรับคำถามและประมวลผลผ่าน OpenRouter API
# ----------------------------------------------------
if user_input := st.chat_input("พิมพ์คำถามเกี่ยวกับสินค้าคอมพิวเตอร์ที่นี่..."):
    # บันทึกคำถามของ User
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # ส่งประมวลผลไปยัง API
    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูลและพิมพ์คำตอบ..."):
            try:
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                # เรียกใช้โมเดลฟรีผ่าน OpenRouter
                response = client.chat.completions.create(
                    model="openrouter/free",
                    messages=api_messages,
                    temperature=0.2
                )

                bot_reply = response.choices[0].message.content
                st.write(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ API: {e}")