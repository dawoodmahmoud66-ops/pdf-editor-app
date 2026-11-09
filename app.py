import io
import os
import gc
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(page_title="حذف صفحات من PDF", layout="wide")

st.title("⚡ معالجة وحذف أوراق PDF (بدون استهلاك ذاكرة السيرفر)")

# إعداد مؤشر الملفات
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0

uploaded_files = st.file_uploader(
    "📁 ارفع الفولدر أو اختر جميع ملفات الـ PDF دفعة واحدة:", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    pdf_files = [f for f in uploaded_files if f.name.lower().endswith('.pdf')]
    total_files = len(pdf_files)

    if total_files == 0:
        st.warning("⚠️ لم يتم العثور على أي ملفات PDF!")
    else:
        if st.session_state.current_file_idx >= total_files:
            st.session_state.current_file_idx = 0

        current_idx = st.session_state.current_file_idx
        current_file = pdf_files[current_idx]

        st.info(f"📂 الملف الحالي ({current_idx + 1} من أصل {total_files}): **{current_file.name}**")
        st.progress((current_idx + 1) / total_files)

        # قراءة بيانات الملف الحالي فقط
        pdf_bytes = current_file.getvalue()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)

        st.write(f"📄 إجمالي الصفحات: **{total_pages}** صفحة")
        st.subheader("🖼️ اختر الصفحات المراد **حذفها**:")

        try:
            # استخدام dpi=72 وحجم مصغر وتقليل أبعاد الصورة لتقليل استهلاك الـ RAM لأدنى حد
            with st.spinner("جاري إعداد المعاينة..."):
                images = convert_from_bytes(pdf_bytes, dpi=72, size=(400, None))

            pages_to_delete = []
            cols_per_row = 4
            cols = st.columns(cols_per_row)

            for index, img in enumerate(images):
                col = cols[index % cols_per_row]
                with col:
                    st.image(img, caption=f"صفحة {index + 1}")
                    if st.checkbox(f"حذف {index + 1}", key=f"f_{current_idx}_p_{index}"):
                        pages_to_delete.append(index)

            st.markdown("---")

            # عملية معالجة وحذف الصفحات
            writer = PdfWriter()
            kept_pages = 0
            for i in range(total_pages):
                if i not in pages_to_delete:
                    writer.add_page(reader.pages[i])
                    kept_pages += 1

            if kept_pages == 0:
                st.error("⚠️ اخترت جميع الصفحات للحذف!")
            else:
                output_pdf = io.BytesIO()
                writer.write(output_pdf)
                output_bytes = output_pdf.getvalue()

                # دالة الانتقال + تفريغ الذاكرة فوراً من الصور القديمة (Garbage Collector)
                def go_next():
                    st.session_state.current_file_idx += 1
                    gc.collect()

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 تحميل الملف والتالي ➡️",
                        data=output_bytes,
                        file_name=f"modified_{os.path.basename(current_file.name)}",
                        mime="application/pdf",
                        on_click=go_next
                    )
                with col2:
                    if st.button("⏭️ تخطي هذا الملف"):
                        st.session_state.current_file_idx += 1
                        gc.collect()
                        st.rerun()

            # مسح الصور من ذاكرة الجهاز مؤقتاً
            del images
            gc.collect()

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

else:
    st.session_state.current_file_idx = 0
    st.write("👈 ارفع الفولدر للبدء.")
