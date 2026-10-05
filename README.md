# 💻 Computer Hardware & Gadget RAG Chatbot

ระบบแชตบอตตอบคำถามสเปก และเช็กราคาสินค้าคอมพิวเตอร์ด้วยเทคนิค Retrieval-Augmented Generation (RAG)

## 📌 หัวข้อและขอบเขต (Domain)
ระบบผู้ช่วยตอบคำถามเกี่ยวกับอุปกรณ์คอมพิวเตอร์ โน้ตบุ๊ก การ์ดจอ และอุปกรณ์เสริม เพื่อช่วยลูกค้าตรวจสอบสเปก ราคา และเงื่อนไขการรับประกัน

## 🛠️ เทคนิค RAG ที่ใช้
1. **Document Chunking:** ใช้ Character-based Overlapping Chunking (Chunk size: 300, Overlap: 50)
2. **Embedding & Vector Search:** ใช้ `paraphrase-multilingual-MiniLM-L12-v2` ร่วมกับ `FAISS` ในการทำ Vector Indexing
3. **Prompt Engineering:** ออกแบบ System Prompt กำหนดให้ LLM ตอบเฉพาะจาก Context เท่านั้น หากไม่มีข้อมูลให้ตอบว่า "ไม่พบข้อมูล"
4. **LLM API:** เรียกใช้งานผ่าน Groq API (`llama-3.3-70b-versatile`)

## 🚀 วิธีเปิดใช้งาน
1. Clone Repository นี้
2. ติดตั้ง Dependencies: `pip install -r requirements.txt`
3. ตั้งค่า API Key ใน `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "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"