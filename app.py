import io
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(page_title="حذف صفحات من PDF", layout="wide")

st.title("✂️ معالجة وحذف أوراق من ملفات PDF (ملف تلو الآخر)")

# إعداد مؤشر الملفات
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0

uploaded_files = st.file_uploader(
    "قم برفع ملفات الـ PDF هنا (يمكنك اختيار أكثر من ملف):", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    total_uploaded = len(uploaded_files)

    if st.session_state.current_file_idx >= total_uploaded:
        st.session_state.current_file_idx = 0

    current_idx = st.session_state.current_file_idx
    current_file = uploaded_files[current_idx]

    st.info(f"📂 الملف الحالي: **{current_file.name}** ({current_idx + 1} من أصل {total_uploaded})")
    st.progress((current_idx + 1) / total_uploaded)

    pdf_bytes = current_file.getvalue()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    st.write(f"📄 إجمالي عدد صفحات هذا الملف: **{total_pages}** صفحة")
    st.subheader("🖼️ اختر الصفحات التي تريد **حذفها** من هذا الملف:")

    try:
        with st.spinner("جاري تحميل معاينة الصفحات..."):
            images = convert_from_bytes(pdf_bytes, dpi=100)

        pages_to_delete = []
        cols_per_row = 4
        cols = st.columns(cols_per_row)

        for index, img in enumerate(images):
            col = cols[index % cols_per_row]
            with col:
                # تم حذف جميع المعاملات الملغاة لمنع التحذيرات نهائياً
                st.image(img, caption=f"صفحة {index + 1}")
                if st.checkbox(f"حذف صفحة {index + 1}", key=f"file_{current_idx}_p_{index}"):
                    pages_to_delete.append(index)

        st.markdown("---")

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
                    label="📥 تحميل الملف الحالي والانتقال للتالي ➡️",
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
        st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

else:
    st.session_state.current_file_idx = 0
    st.write("👈 يرجى رفع ملفات PDF للبدء.")
