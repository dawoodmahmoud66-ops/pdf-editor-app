import io
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(page_title="حذف صفحات من PDF", layout="wide")

st.title("📄 تطبيق حذف واختيار صفحات من ملف PDF")

# رفع ملف الـ PDF
uploaded_file = st.file_uploader("قم برفع ملف الـ PDF هنا", type=["pdf"])

if uploaded_file is not None:
  # قراءة الملف
  pdf_bytes = uploaded_file.read()
  reader = PdfReader(io.BytesIO(pdf_bytes))
  total_pages = len(reader.pages)

  st.info(f"إجمالي عدد الصفحات: {total_pages}")

  st.subheader("🖼️ اختر الصفحات التي تريد **حذفها**:")

  # تحويل صفحات الـ PDF إلى صور للعرض (مع تسريع التحميل)
  with st.spinner("جاري تحميل معاينة الصفحات..."):
    images = convert_from_bytes(pdf_bytes, dpi=72)

  # عرض الصفحات في شبكة
  pages_to_delete = []
  cols_per_row = 4  # عدد الصور في كل صف

  cols = st.columns(cols_per_row)
  for index, img in enumerate(images):
    col = cols[index % cols_per_row]
    with col:
      st.image(img, caption=f"صفحة {index + 1}", use_container_width=True)
      if st.checkbox(f"حذف صفحة {index + 1}", key=f"page_{index}"):
        pages_to_delete.append(index)

  st.markdown("---")

  # زر معالجة الملف
  if st.button("✂️ تنفيذ الحذف وإنشاء الملف الجديد"):
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

      st.success(
          f"تم حذف {len(pages_to_delete)} صفحة بنجاح! المتبقي: {kept_pages}"
          " صفحة."
      )

      st.download_button(
          label="📥 تحميل ملف PDF المعدل",
          data=output_pdf,
          file_name=f"modified_{uploaded_file.name}",
          mime="application/pdf",
      )
