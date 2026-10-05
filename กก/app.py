import os
import glob
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="ผู้ช่วยตอบคำถามและเช็กราคาสินค้าคอมพิวเตอร์",
    page_icon="💻",
    layout="centered"
)

st.title("💻 ผู้ช่วยตอบคำถามและเช็กราคาสินค้าคอมพิวเตอร์")
st.caption("ระบบแชตบอต RAG ตอบคำถามสเปก ราคา และการใช้งานจากคลังข้อมูลสินค้า")

if "OPENROUTER_API_KEY" not in st.secrets:
    st.error("❌ ไม่พบ OPENROUTER_API_KEY ในไฟล์ .streamlit/secrets.toml")
    st.stop()

# เชื่อมต่อ OpenRouter ผ่าน OpenAI Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
)

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

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "สวัสดีครับ! สอบถามข้อมูลสเปก ราคา หรือการใช้งานคอมพิวเตอร์และอุปกรณ์ไอทีได้เลยครับ"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_input := st.chat_input("พิมพ์คำถามเกี่ยวกับสินค้าคอมพิวเตอร์ที่นี่..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูลและพิมพ์คำตอบ..."):
            try:
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                # ใช้ตัวเลือก openrouter/free ซึ่งระบบจะจับคู่โมเดลฟรีที่พร้อมที่สุดให้อัตโนมัติ
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