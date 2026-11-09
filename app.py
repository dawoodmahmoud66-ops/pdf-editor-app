import io
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(page_title="حذف صفحات من ملفات PDF متعددة", layout="wide")

st.title("✂️ معالجة وحذف أوراق من ملفات PDF (ملف تلو الآخر)")

# 1. إعداد قائمة المتغيرات في الـ Session State للحفاظ على حالة التنقل
if "current_file_idx" not in st.session_state:
    st.session_state.current_file_idx = 0

# 2. رفع عدة ملفات دفعة واحدة (accept_multiple_files=True)
uploaded_files = st.file_uploader(
    "قم برفع ملفات الـ PDF هنا (يمكنك اختيار أكثر من ملف):", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    total_uploaded = len(uploaded_files)

    # إعادة الضبط في حال كانت القائمة تفيض عن عدد الملفات المرفوعة
    if st.session_state.current_file_idx >= total_uploaded:
        st.session_state.current_file_idx = 0

    current_idx = st.session_state.current_file_idx
    current_file = uploaded_files[current_idx]

    # عرض شريط التقدم ونسبة الإنجاز
    st.info(f"📂 الملف الحالي: **{current_file.name}** ({current_idx + 1} من أصل {total_uploaded})")
    st.progress((current_idx + 1) / total_uploaded)

    # قراءة الملف الحالي
    pdf_bytes = current_file.read()
    current_file.seek(0)  # إعادة ضبط مؤشر الملف
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    st.write(f"📄 إجمالي عدد صفحات هذا الملف: **{total_pages}** صفحة")
    st.subheader("🖼️ اختر الصفحات التي تريد **حذفها** من هذا الملف:")

    # تحويل صفحات الملف إلى صور بدقة 150 DPI للوضوح
    with st.spinner("جاري تحميل معاينة الصفحات بجودة عالية..."):
        images = convert_from_bytes(pdf_bytes, dpi=150)

    pages_to_delete = []
    cols_per_row = 4

    cols = st.columns(cols_per_row)
    for index, img in enumerate(images):
        col = cols[index % cols_per_row]
        with col:
            st.image(img, caption=f"صفحة {index + 1}", use_container_width=True)
            # مفتاح ديناميكي لمنع تداخل الاختيارات بين الملفات (key يتضمن اسم الملف ورقم الصفحة)
            if st.checkbox(f"حذف صفحة {index + 1}", key=f"{current_file.name}_p_{index}"):
                pages_to_delete.append(index)

    st.markdown("---")

    # زر معالجة الصفحات المحددة
    if st.button("✂️ تنفيذ الحذف وتجهيز التحميل"):
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
            output_pdf.seek(0)

            st.session_state.processed_data = output_pdf.getvalue()
            st.session_state.ready_to_download = True
            st.success(f"تم حذف {len(pages_to_delete)} صفحة بنجاح! المتبقي: {kept_pages} صفحة.")

    # إظهار زر التحميل والانتقال التلقائي للملف التالي
    if st.session_state.get("ready_to_download", False):
        
        # دالة لزيادة المؤشر والانتقال للملف التالي عند ضغط التحميل
        def next_file():
            st.session_state.current_file_idx += 1
            st.session_state.ready_to_download = False

        st.download_button(
            label="📥 تحميل ملف PDF المعدل والانتقال للملف التالي ➡️",
            data=st.session_state.processed_data,
            file_name=f"modified_{current_file.name}",
            mime="application/pdf",
            on_click=next_file
        )

    # زر لتخطي الملف الحالي دون تعديل إذا أردت
    if st.button("⏭️ تخطي هذا الملف والانتقال للتالي"):
        st.session_state.current_file_idx += 1
        st.session_state.ready_to_download = False
        st.rerun()

else:
    # إعادة ضبط الحالة في حال حذف الملفات المرفوعة
    st.session_state.current_file_idx = 0
    st.session_state.ready_to_download = False
    st.write("👈 يرجى رفع ملفات PDF للبدء.")
