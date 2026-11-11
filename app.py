import io
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import streamlit as st
import pandas as pd
import gc

st.set_page_config(page_title="حذف صفحات من PDF", layout="wide")

# 🎨 تطبيق الخلفية السوداء والنصوص البيضاء
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #262730;
        color: #FFFFFF;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ معالجة وحذف أوراق PDF (مع ضغط الجودة وتقليل الحجم)")

# رفع الملفات
uploaded_files = st.file_uploader(
    "📁 ارفع ملفات الـ PDF (اختر الملفات المطلوبة):", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    if "processed_file_names" not in st.session_state:
        st.session_state.processed_file_names = set()
    if "report_data" not in st.session_state:
        st.session_state.report_data = []

    # تصفية الملفات للحصول على المتبقي فقط
    remaining_files = [f for f in uploaded_files if f.name not in st.session_state.processed_file_names]
    
    total_original = len(uploaded_files)
    completed_count = len(st.session_state.processed_file_names)

    # حالة الانتهاء من كافة الملفات
    if not remaining_files:
        st.balloons()
        st.success(f"🎉 تم الانتهاء من معالجة جميع الملفات بنجاح! ({completed_count} من أصل {total_original})")
        
        if st.session_state.report_data:
            df_report = pd.DataFrame(st.session_state.report_data)
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_report.to_excel(writer, index=False, sheet_name='تقرير الملفات')
            excel_data = excel_buffer.getvalue()

            st.download_button(
                label="📊 تحميل تقرير Excel لجميع الملفات المعدلة",
                data=excel_data,
                file_name="pdf_processing_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.markdown("---")
        if st.button("🔄 بدء معالجة قائمة جديدة"):
            st.session_state.processed_file_names = set()
            st.session_state.report_data = []
            gc.collect()
            st.rerun()

    else:
        current_file = remaining_files[0]

        st.info(f"📂 الملف الحالي ({completed_count + 1} من أصل {total_original}): **{current_file.name}**")
        st.progress(completed_count / total_original)

        pdf_bytes = current_file.getvalue()

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)

            st.write(f"📄 إجمالي الصفحات الأصلي: **{total_pages}** صفحة")
            st.subheader("🖼️ اختر الصفحات المراد **حذفها**:")

            pages_to_delete = []
            cols_per_row = 4
            cols = st.columns(cols_per_row)

            # 1. معاينة الصفحات بدقة خفيفة للواجهة
            for index in range(total_pages):
                page = doc.load_page(index)
                pix = page.get_pixmap(dpi=40)
                img_bytes = pix.tobytes("jpeg")

                col = cols[index % cols_per_row]
                with col:
                    st.image(img_bytes, caption=f"صفحة {index + 1}")
                    if st.checkbox(f"حذف {index + 1}", key=f"{current_file.name}_p_{index}"):
                        pages_to_delete.append(index)

            st.markdown("---")

            kept_pages_count = total_pages - len(pages_to_delete)

            if kept_pages_count == 0:
                st.error("⚠️ لقد قمت بتحديد جميع الصفحات للحذف!")
            else:
                # 2. إنشاء مستند جديد وضغط الصفحات المتبقية (تقليل الجودة والحجم)
                new_doc = fitz.open()
                
                for index in range(total_pages):
                    if index not in pages_to_delete:
                        page = doc.load_page(index)
                        # تحويل الصفحة لصورة بدقة مخصصة (dpi=120 لضمان خفض الحجم مع وضوح النصوص)
                        pix = page.get_pixmap(dpi=120)
                        img_data = pix.tobytes("jpeg", jpg_quality=65) # ضغط الجودة لـ 65%
                        
                        # إنشاء صفحة جديدة بنفس المقاسات وإعادة رسم الصورة المضغوطة عليها
                        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                        new_page.insert_image(page.rect, stream=img_data)

                # حفظ المستند الناتج بضغط عالي
                output_pdf = io.BytesIO()
                new_doc.save(output_pdf, deflate=True, garbage=4)
                output_bytes = output_pdf.getvalue()
                
                new_doc.close()
                doc.close()
                gc.collect()

                # دوال حفظ الحسابات والانتقال
                def mark_current_as_processed():
                    st.session_state.report_data.append({
                        "اسم الملف": current_file.name,
                        "عدد الصفحات بعد الحذف": kept_pages_count,
                        "عدد الصفحات المحذوفة": len(pages_to_delete),
                        "عدد الصفحات الأصلي": total_pages
                    })
                    st.session_state.processed_file_names.add(current_file.name)
                    gc.collect()

                def skip_current_file():
                    st.session_state.processed_file_names.add(current_file.name)
                    gc.collect()

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 تحميل الملف المضغوط والتالي ➡️",
                        data=output_bytes,
                        file_name=current_file.name,
                        mime="application/pdf",
                        on_click=mark_current_as_processed
                    )
                with col2:
                    if st.button("⏭️ تخطي هذا الملف", on_click=skip_current_file):
                        st.rerun()

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
            gc.collect()

else:
    st.session_state.processed_file_names = set()
    st.session_state.report_data = []
    gc.collect()
    st.write("👈 قم برفع الملفات للبدء.")
