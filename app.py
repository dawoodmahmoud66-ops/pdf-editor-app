import io
import fitz  # PyMuPDF: أسرع وأخف مكتبة لمعاينة صفحات الـ PDF
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(page_title="حذف صفحات من PDF", layout="wide")

st.title("⚡ معالجة وحذف أوراق PDF (بدون استهلاك الذاكرة)")

# إعداد مؤشر الملف الحالي
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0

uploaded_files = st.file_uploader(
    "📁 ارفع ملفات الـ PDF (اختر الملفات المطلوبة):", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    total_files = len(uploaded_files)

    if st.session_state.current_file_idx >= total_files:
        st.session_state.current_file_idx = 0

    current_idx = st.session_state.current_file_idx
    current_file = uploaded_files[current_idx]

    st.info(f"📂 الملف الحالي ({current_idx + 1} من أصل {total_files}): **{current_file.name}**")
    st.progress((current_idx + 1) / total_files)

    # قراءة الملف الحقيقي بدون تخزين دائم
    pdf_bytes = current_file.getvalue()

    try:
        # قراءة معالجة الصفحات عبر PyMuPDF (سريعة وخفيفة على السيرفر)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        st.write(f"📄 إجمالي الصفحات: **{total_pages}** صفحة")
        st.subheader("🖼️ اختر الصفحات المراد **حذفها**:")

        pages_to_delete = []
        cols_per_row = 4
        cols = st.columns(cols_per_row)

        for index in range(total_pages):
            page = doc.load_page(index)
            pix = page.get_pixmap(dpi=80)  # معاينة فائقة السرعة
            img_bytes = pix.tobytes("png")

            col = cols[index % cols_per_row]
            with col:
                st.image(img_bytes, caption=f"صفحة {index + 1}")
                if st.checkbox(f"حذف {index + 1}", key=f"f_{current_idx}_p_{index}"):
                    pages_to_delete.append(index)

        doc.close()
        st.markdown("---")

        # معالجة ملف الـ PDF الجديد
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        kept_pages = 0

        for i in range(total_pages):
            if i not in pages_to_delete:
                writer.add_page(reader.pages[i])
                kept_pages += 1

        if kept_pages == 0:
            st.error("⚠️ لقد قمت بتحديد جميع الصفحات للحذف!")
        else:
            output_pdf = io.BytesIO()
            writer.write(output_pdf)
            output_bytes = output_pdf.getvalue()

            def go_next():
                st.session_state.current_file_idx += 1

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 تحميل الملف والتالي ➡️",
                    data=output_bytes,
                    file_name=f"modified_{current_file.name}",
                    mime="application/pdf",
                    on_click=go_next
                )
            with col2:
                if st.button("⏭️ تخطي هذا الملف"):
                    st.session_state.current_file_idx += 1
                    st.rerun()

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

else:
    st.session_state.current_file_idx = 0
    st.write("👈 قم برفع الملفات للبدء.")
